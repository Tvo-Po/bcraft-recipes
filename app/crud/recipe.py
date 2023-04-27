from datetime import timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import case, delete, func, Result, select, Select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.database.tools import FilterConditionChain
from app.model.recipe import (
    Ingredient,
    Recipe,
    RecipeIngredientAssociation,
    Step,
    RecipeRate,
)


def filter_ingredients(ingredient_names: set[str]):
    matched_ingredient = case(
        (Ingredient.name.in_(ingredient_names), 1), 
        else_=0,
    )
    return select(Recipe).with_only_columns(Recipe.id) \
           .join(Recipe.ingredients) \
           .join(RecipeIngredientAssociation.ingredient) \
           .group_by(Recipe.id) \
           .having(
               func.sum(matched_ingredient) == len(ingredient_names)
           )


def get_recipe_list_query(
    duration__lte: timedelta | None = None,
    duration__gte: timedelta | None = None,
    rating__lte: float |  None = None,
    rating__gte: float |  None = None,
    ingredient_names: set[str] | None = None,
) -> Select[tuple[Recipe, timedelta, float]]:
    step_sq = select(
        Step.recipe_id,
        func.sum(Step.duration).label('total_duration'),
    ).group_by(Step.recipe_id).subquery()
    rate_sq = select(
        RecipeRate.recipe_id,
        func.avg(RecipeRate.rate).label('rating'),
    ).group_by(RecipeRate.recipe_id).subquery()
    total_duration_column = func.coalesce(
        step_sq.c.total_duration,
        timedelta(seconds=0),
    )
    rating_column = func.coalesce(rate_sq.c.rating, 0)
    filters = FilterConditionChain(
        None if duration__lte is None else
        total_duration_column <= duration__lte
    ) & (
        None if duration__gte is None else
        total_duration_column >= duration__gte
    ) & (
        None if ingredient_names is None else
        Recipe.id.in_(filter_ingredients(ingredient_names))
    ) & (
        None if rating__lte is None else
        rating_column <= rating__lte
    ) & (
        None if rating__gte is None else
        rating_column >= rating__gte
    )
    return filters.resolve(
        select(
            Recipe,
            total_duration_column,
            rating_column,
        ).join(step_sq) \
         .outerjoin(rate_sq) \
         .join(Recipe.ingredients) \
         .join(RecipeIngredientAssociation.ingredient) \
         .options(
             contains_eager(Recipe.ingredients)
            .contains_eager(RecipeIngredientAssociation.ingredient)
            .load_only(Ingredient.name)
        )
    )


async def create_recipe(
    data: dict[str, Any],
    session: AsyncSession,
) -> Recipe:
    ingredient_names = data.pop('ingredients')
    existing_ingredients = cast(list[Ingredient],
            (
            await session.execute(
                select(Ingredient)
            .filter(Ingredient.name.in_(ingredient_names))
            )
        ).scalars().all()
    )
    new_ingredients = [
        Ingredient(name=name) for name in
        ingredient_names - {i.name for i in existing_ingredients}
    ]
    existing_ingredients.extend(new_ingredients)
    steps = [Step(**data) for data in data.pop('steps')]
    recipe = Recipe(**data)
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in existing_ingredients
    ]
    session.add(recipe)
    session.add_all(new_ingredients)
    await session.commit()
    return recipe


async def _get_recipe_result(
    id: int,
    session: AsyncSession,
) -> Result[tuple[Recipe]]:
    return await session.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredientAssociation.ingredient)
        )
        .options(selectinload(Recipe.steps))
        .filter_by(id=id)
    )


async def get_recipe(
    id: int,
    session: AsyncSession,
) -> Recipe:
    result = await _get_recipe_result(id, session)
    return result.scalar_one()


async def edit_recipe(
    id: int,
    data: dict[str, Any],
    session: AsyncSession,
) -> Recipe:
    ingredient_names = data.pop('ingredients')
    existing_ingredients = cast(list[Ingredient],
            (
            await session.execute(
                select(Ingredient)
            .filter(Ingredient.name.in_(ingredient_names))
            )
        ).scalars().all()
    )
    new_ingredients = [
        Ingredient(name=name) for name in
        ingredient_names - {i.name for i in existing_ingredients}
    ]
    existing_ingredients.extend(new_ingredients)
    result = await _get_recipe_result(id, session)
    recipe = result.scalar_one()
    steps = [Step(**data) for data in data.pop('steps')]
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in existing_ingredients
    ]
    session.add(recipe)
    session.add_all(new_ingredients)
    await session.commit()
    return recipe


async def delete_recipe(
    id: int,
    session: AsyncSession,
):
    await session.execute(delete(Recipe).filter_by(id=id))
    await session.commit()


async def rate_recipe(
    recipe_id: int,
    user_id: UUID,
    rate: int,
    session: AsyncSession,
):
    session.add(RecipeRate(recipe_id=recipe_id, user_id=user_id, rate=rate))
    await session.commit()
