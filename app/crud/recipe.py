from datetime import timedelta
from typing import Any, cast
from uuid import UUID

from asyncpg.exceptions import ForeignKeyViolationError  # type: ignore
from sqlalchemy import case, delete, func, Result, select, Select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.sql import SQLColumnExpression

from app.database.tools import FilterConditionChain
from app.model.recipe import (
    Ingredient,
    Recipe,
    RecipeIngredientAssociation,
    Step,
    RecipeRate,
)


def _get_query_with_recipe_ids_containing_all_given_ingredients(
    ingredient_names: set[str],
):
    matched_ingredient = case(
        (Ingredient.name.in_(ingredient_names), 1),
        else_=0,
    )
    return (
        select(Recipe)
        .with_only_columns(Recipe.id)
        .join(Recipe.ingredients)
        .join(RecipeIngredientAssociation.ingredient)
        .group_by(Recipe.id)
        .having(func.sum(matched_ingredient) == len(ingredient_names))
    )


def _get_filters(
    duration_column: SQLColumnExpression,
    rating_column: SQLColumnExpression,
    id_column: SQLColumnExpression,
    duration__lte: timedelta | None = None,
    duration__gte: timedelta | None = None,
    rating__lte: float | None = None,
    rating__gte: float | None = None,
    ingredient_names: set[str] | None = None,
) -> FilterConditionChain:
    filters = (
        FilterConditionChain(
            None if duration__lte is None else duration_column <= duration__lte
        )
        & (None if duration__gte is None else duration_column >= duration__gte)
        & (
            None
            if ingredient_names is None
            else id_column.in_(
                _get_query_with_recipe_ids_containing_all_given_ingredients(
                    ingredient_names
                )
            )
        )
        & (None if rating__lte is None else rating_column <= rating__lte)
        & (None if rating__gte is None else rating_column >= rating__gte)
    )
    return filters


def apply_order(
    query: Select,
    duration_column: SQLColumnExpression,
    rating_column: SQLColumnExpression,
    order: str | None,
) -> Select:
    if order is None:
        return query
    if 'duration' in order:
        c = duration_column if order[0] != '-' else duration_column.desc()
        return query.order_by(c)
    if 'rating' in order:
        c = rating_column if order[0] != '-' else rating_column.desc()
        return query.order_by(c)
    raise ValueError('Unexpected order parameter.')


def get_recipe_list_query(
    duration__lte: timedelta | None = None,
    duration__gte: timedelta | None = None,
    rating__lte: float | None = None,
    rating__gte: float | None = None,
    ingredient_names: set[str] | None = None,
    order: str | None = None,
) -> Select[tuple[Recipe, timedelta, float]]:
    step_sq = (
        select(
            Step.recipe_id,
            func.sum(Step.duration).label('total_duration'),
        )
        .group_by(Step.recipe_id)
        .subquery()
    )
    rate_sq = (
        select(
            RecipeRate.recipe_id,
            func.avg(RecipeRate.rate).label('rating'),
        )
        .group_by(
            RecipeRate.recipe_id,
        )
        .subquery()
    )
    total_duration_column = func.coalesce(
        step_sq.c.total_duration,
        timedelta(seconds=0),
    )
    rating_column = func.coalesce(rate_sq.c.rating, 0)
    filters = _get_filters(
        total_duration_column,
        rating_column,
        Recipe.id,
        duration__lte,
        duration__gte,
        rating__lte,
        rating__gte,
        ingredient_names,
    )
    return apply_order(
        filters.resolve(
            select(
                Recipe,
                total_duration_column,
                rating_column,
            )
            .join(step_sq)
            .outerjoin(rate_sq)
            .join(Recipe.ingredients)
            .join(RecipeIngredientAssociation.ingredient)
            .options(
                contains_eager(Recipe.ingredients)
                .contains_eager(RecipeIngredientAssociation.ingredient)
                .load_only(Ingredient.name)
            )
        ),
        total_duration_column,
        rating_column,
        order,
    )


async def _get_recipe_result(
    id: int,
    session: AsyncSession,
) -> Result[tuple[Recipe]]:
    return (
        await session.execute(
            select(Recipe)
            .options(
                joinedload(Recipe.ingredients).joinedload(
                    RecipeIngredientAssociation.ingredient
                )
            )
            .options(joinedload(Recipe.steps))
            .filter_by(id=id)
        )
    ).unique()


async def get_recipe(
    id: int,
    session: AsyncSession,
) -> Recipe:
    result = await _get_recipe_result(id, session)
    return result.scalar_one()


async def _get_existing_and_new_ingredients_from_names(
    ingredient_names: set[str],
    session: AsyncSession,
) -> tuple[list[Ingredient], list[Ingredient]]:
    existing_ingredients = cast(
        list[Ingredient],
        (
            await session.execute(
                select(Ingredient).filter(Ingredient.name.in_(ingredient_names))
            )
        )
        .scalars()
        .all(),
    )
    new_ingredients = [
        Ingredient(name=name)
        for name in ingredient_names - {i.name for i in existing_ingredients}
    ]
    return existing_ingredients, new_ingredients


async def _update_entire_recipe(
    recipe: Recipe,
    steps: list[Step],
    ingredient_names: set[str],
    session: AsyncSession,
):
    existing, new = await _get_existing_and_new_ingredients_from_names(
        ingredient_names,
        session,
    )
    all_ingredients = existing + new
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in all_ingredients
    ]
    session.add(recipe)
    session.add_all(new)
    await session.commit()
    return recipe


async def create_recipe(
    data: dict[str, Any],
    session: AsyncSession,
) -> Recipe:
    ingredient_names = data.pop('ingredients')
    steps = [Step(**data) for data in data.pop('steps')]
    recipe = Recipe(**data)
    return await _update_entire_recipe(
        recipe,
        steps,
        ingredient_names,
        session,
    )


async def edit_recipe(
    id: int,
    data: dict[str, Any],
    session: AsyncSession,
) -> Recipe:
    result = await _get_recipe_result(id, session)
    recipe = result.scalar_one()
    steps = [Step(**data) for data in data.pop('steps')]
    ingredient_names = data.pop('ingredients')
    return await _update_entire_recipe(
        recipe,
        steps,
        ingredient_names,
        session,
    )


async def delete_recipe(
    id: int,
    engine: AsyncEngine,
):
    async with engine.connect() as conn:
        result = await conn.execute(delete(Recipe).filter_by(id=id))
    if result.rowcount == 0:
        raise NoResultFound("Recipe with given id not found.")


async def rate_recipe(
    recipe_id: int,
    user_id: UUID,
    rate: int,
    session: AsyncSession,
):
    try:
        session.add(RecipeRate(recipe_id=recipe_id, user_id=user_id, rate=rate))
        await session.commit()
    except IntegrityError as exc:
        try:
            if isinstance(exc.__cause__.__cause__, ForeignKeyViolationError):  # type: ignore
                raise NoResultFound("Recipe with given id not found.")
            raise exc
        except AttributeError:
            raise exc
