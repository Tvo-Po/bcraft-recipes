from typing import Any, Optional

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import delete, Result, select, Select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from .model import (
    Ingredient,
    Recipe,
    RecipeIngredientAssociation,
    Step,
)


class IngridientFilter(Filter):
    name__in: Optional[list[str]]
    
    class Constants(Filter.Constants):
        model = Ingredient


class RecipeFilter(Filter):
    ingridients: Optional[IngridientFilter] = FilterDepends(with_prefix(
        'ingridients', IngridientFilter
    ))
    
    class Constants(Filter.Constants):
        model = Recipe


def get_recipe_list_query() -> Select[tuple[Recipe]]:
    return select(Recipe) \
           .join(Recipe.ingredients) \
           .join(RecipeIngredientAssociation.ingredient) \
           .options(
                contains_eager(Recipe.ingredients)
                .contains_eager(RecipeIngredientAssociation.ingredient)
                .load_only(Ingredient.name)
           )


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
