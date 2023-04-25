from fastapi import Depends, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud
from .db import get_session
from .schema import (
    FullRecipeData,
    RecipeEntityResponse,
    RecipeListResponse,
)

router = APIRouter(prefix='/api/v1')


@router.get('/recipe')
async def get_recipe_list(
    session: AsyncSession = Depends(get_session),
) -> list[RecipeListResponse]:
    return await crud.get_recipe_list(session)


@router.post('/recipe', status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
) -> RecipeEntityResponse:
    return await crud.create_recipe(data, session)


@router.get('/recipe/{id}')
async def get_recipe(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> RecipeEntityResponse:
    return await crud.get_recipe(id, session)


@router.put('/recipe/{id}')
async def edit_recipe(
    id: int,
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
) -> RecipeEntityResponse:
    return await crud.edit_recipe(id, data, session)


@router.delete('/recipe/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_recipe(id, session)
