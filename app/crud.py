from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import (
    CreateRecipeData,
    RecipeEntityResponse,
)
from .model import (
    Ingredient,
    Recipe,
    RecipeIngredientAssociation,
    Step,
)


async def create_recipe(
    data: CreateRecipeData,
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
    
    