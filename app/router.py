from typing import Any, cast

from fastapi import Depends, status
from fastapi.routing import APIRouter
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud
from .config import settings
from .db import get_session
from .schema import (
    FullRecipeData,
    RecipeEntityResponse,
    RecipeListResponse,
)

router = APIRouter(prefix='/api/v1')


@router.get('/recipe', response_model=Page[RecipeListResponse])
async def get_recipe_list(
    filter: crud.RecipeFilter = FilterDepends(crud.RecipeFilter),
    session: AsyncSession = Depends(get_session),
):
    return await paginate(
        session,
        cast(Select[Any], filter.filter(crud.get_recipe_list_query())),
    )


@router.post(
    '/recipe',
    response_model=RecipeEntityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe(
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
):
    return await crud.create_recipe(data.dict(), session)


@router.get('/recipe/{id}', response_model=RecipeEntityResponse)
async def get_recipe(id: int, session: AsyncSession = Depends(get_session)):
    return await crud.get_recipe(id, session)


@router.put('/recipe/{id}', response_model=RecipeEntityResponse)
async def edit_recipe(
    id: int,
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
):
    return await crud.edit_recipe(id, data.dict(), session)


@router.delete('/recipe/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_recipe(id, session)
