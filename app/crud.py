from sqlalchemy import delete, Result, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .schema import (
    FullRecipeData,
    RecipeEntityResponse,
    RecipeListResponse,
)
from .model import (
    Ingredient,
    Recipe,
    RecipeIngredientAssociation,
    Step,
)


async def get_recipe_list(
    session: AsyncSession,
) -> list[RecipeListResponse]:
    recipes = await session.execute(select(Recipe))
    return [
        RecipeListResponse.from_orm(recipe)
        for recipe in recipes.scalars().all()
    ]


async def create_recipe(
    data: FullRecipeData,
    session: AsyncSession,
) -> RecipeEntityResponse:
    recipe_dict = data.dict()
    ingredients = [
        Ingredient(name=name) for name in recipe_dict.pop('ingredients')
    ]
    steps = [Step(**data) for data in recipe_dict.pop('steps')]
    recipe = Recipe(**recipe_dict)
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in ingredients
    ]
    session.add(recipe)
    session.add_all(ingredients)
    await session.commit()
    return RecipeEntityResponse.from_orm(recipe)


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
) -> RecipeEntityResponse:
    result = await _get_recipe_result(id, session)
    return RecipeEntityResponse.from_orm(result.one())


async def edit_recipe(
    id: int,
    data: FullRecipeData,
    session: AsyncSession,
) -> RecipeEntityResponse:
    result = await _get_recipe_result(id, session)
    recipe = result.scalar_one()
    recipe_dict = data.dict()
    ingredients = [
        Ingredient(name=name) for name in recipe_dict.pop('ingredients')
    ]
    steps = [Step(**data) for data in recipe_dict.pop('steps')]
    recipe.steps = steps
    recipe.ingredients = [
        RecipeIngredientAssociation(ingredient=ingredient)
        for ingredient in ingredients
    ]
    session.add(recipe)
    session.add_all(ingredients)
    await session.commit()
    return RecipeEntityResponse.from_orm(recipe)


async def delete_recipe(
    id: int,
    session: AsyncSession,
):
    await session.execute(delete(Recipe).filter_by(id=id))
    await session.commit()
