from datetime import timedelta

from fastapi import Depends, status, Query
from fastapi.routing import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


from .schema import (
    FullRecipeData,
    RateData,
    RecipeEntityResponse,
    RecipeListOrder,
    RecipeListResponse,
)
from app.api.auth.dependency import get_authenticated_user
from app.api.auth.schema import AuthUser
from app.crud import recipe as crud
from app.database.tools import get_engine, get_session


router = APIRouter()
public_router = APIRouter(prefix='/recipe', tags=['recipe'])
auth_only_router = APIRouter(
    prefix='/recipe',
    tags=['recipe'],
    dependencies=[Depends(get_authenticated_user)],
)


@public_router.get('', response_model=Page[RecipeListResponse])
async def get_recipe_list(
    duration__lte: timedelta | None = Query(default=None),
    duration__gte: timedelta | None = Query(default=None),
    rating__lte: float | None = Query(default=None),
    rating__gte: float | None = Query(default=None),
    ingredients: set[str] | None = Query(default=None),
    order: RecipeListOrder | None = Query(default=None),
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
            order,
        ),
    )


@auth_only_router.post(
    '',
    response_model=RecipeEntityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe(
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
):
    return await crud.create_recipe(data.dict(), session)


@public_router.get('/{id}', response_model=RecipeEntityResponse)
async def get_recipe(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    return await crud.get_recipe(id, session)


@auth_only_router.put('/{id}', response_model=RecipeEntityResponse)
async def edit_recipe(
    id: int,
    data: FullRecipeData,
    session: AsyncSession = Depends(get_session),
):
    return await crud.edit_recipe(id, data.dict(), session)


@auth_only_router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(id: int, engine: AsyncEngine = Depends(get_engine)):
    await crud.delete_recipe(id, engine)


@auth_only_router.post('/{id}/rate', status_code=status.HTTP_204_NO_CONTENT)
async def rate_recipe(
    id: int,
    data: RateData,
    user: AuthUser = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
):
    await crud.rate_recipe(id, user.id, data.rate, session)


router.include_router(public_router)
router.include_router(auth_only_router)
