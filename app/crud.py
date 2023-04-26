from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, delete, func, Result, select, Select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from .model import (
    Ingredient,
    Recipe,
    RecipeIngredientAssociation,
    Step,
    RecipeRate,
)


class ConditionsCombiner:
    def __init__(self):
        self.complex_condition = None
    
    def add(self, condition):
        if condition is None:
            return self
        if self.complex_condition is None:
            self.complex_condition = condition
            return self
        self.complex_condition &= condition
        return self


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
    applied_filter = ConditionsCombiner().add(
        duration__lte and
        total_duration_column <= duration__lte
    ).add(
        duration__gte and
        total_duration_column >= duration__gte
    ).add(
        ingredient_names and
        Recipe.id.in_(filter_ingredients(ingredient_names))
    ).add(
        rating__lte and
        rating_column <= rating__lte
    ).add(
        rating__gte and
        rating_column >= rating__gte
    )
    query = select(
                Recipe,
                total_duration_column,
                rating_column,
            ) \
           .join(step_sq) \
           .outerjoin(rate_sq) \
           .join(Recipe.ingredients) \
           .join(RecipeIngredientAssociation.ingredient) \
           .options(
                contains_eager(Recipe.ingredients)
                .contains_eager(RecipeIngredientAssociation.ingredient)
                .load_only(Ingredient.name),
           )
    if applied_filter.complex_condition is None:
        return query
    return query.filter(applied_filter.complex_condition)


async def create_recipe(
    data: dict[str, Any],
    session: AsyncSession,
) -> Recipe:
    ingredients = [
        Ingredient(name=name) for name in data.pop('ingredients')
    ]
    steps = [Step(**data) for data in data.pop('steps')]
    recipe = Recipe(**data)
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in ingredients
    ]
    session.add(recipe)
    session.add_all(ingredients)
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
    result = await _get_recipe_result(id, session)
    recipe = result.scalar_one()
    ingredients = [Ingredient(name=name) for name in data.pop('ingredients')]
    steps = [Step(**data) for data in data.pop('steps')]
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in ingredients
    ]
    session.add(recipe)
    session.add_all(ingredients)
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
