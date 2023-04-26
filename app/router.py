from datetime import timedelta

from fastapi import Depends, status, Query
from fastapi.routing import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession


from . import crud
from .auth import auth_backend, fastapi_users, current_active_user
from .db import get_session
from .schema import (
    FullRecipeData,
    RateData,
    RecipeEntityResponse,
    RecipeListResponse,
    UserCreate,
    UserRead,
)
from .model import User


router = APIRouter(prefix='/api/v1')


router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix='/auth/jwt', tags=['auth']
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)


public_recipe_router = APIRouter(
    prefix='/recipe',
    tags=['recipe'],
)

private_recipe_router = APIRouter(
    prefix='/recipe',
    tags=['recipe'],
    dependencies=[Depends(current_active_user)],
)


@public_recipe_router.get('', response_model=Page[RecipeListResponse])
async def get_recipe_list(
    duration__lte: timedelta | None = Query(default=None),
    duration__gte: timedelta | None = Query(default=None),
    rating__lte: float | None = Query(default=None),
    rating__gte: float | None = Query(default=None),
    ingredients: set[str] | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    return await paginate(
        session,
        crud.get_recipe_list_query(
            duration__lte,
            duration__gte,
            rating__lte,
            rating__gte,
            ingredients,    
        ),
    )


@private_recipe_router.post(
    '',
    response_model=RecipeEntityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe(
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
):
    return await crud.create_recipe(data.dict(), session)


@public_recipe_router.get('/{id}', response_model=RecipeEntityResponse)
async def get_recipe(id: int, session: AsyncSession = Depends(get_session)):
    return await crud.get_recipe(id, session)


@private_recipe_router.put('/{id}', response_model=RecipeEntityResponse)
async def edit_recipe(
    id: int,
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
):
    return await crud.edit_recipe(id, data.dict(), session)


@private_recipe_router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_recipe(id, session)


@private_recipe_router.post('/{id}/rate', status_code=status.HTTP_204_NO_CONTENT)
async def rate_recipe(
    id: int,
    data: RateData,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    await crud.rate_recipe(id, user.id, data.rate, session)


router.include_router(public_recipe_router)
router.include_router(private_recipe_router)
