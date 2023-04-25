from fastapi import Depends
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud
from .db import get_session
from .schema import (
    CreateRecipeData,
    RecipeEntityResponse,
)

router = APIRouter(prefix='/api/v1')


@router.post('/recipe')
async def create_recipe(
    data: CreateRecipeData,
    session: AsyncSession = Depends(get_session),
) -> RecipeEntityResponse:
    return await crud.create_recipe(data, session)
