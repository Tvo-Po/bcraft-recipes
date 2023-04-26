from datetime import timedelta
from typing import Any
import uuid

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field
from pydantic.utils import GetterDict


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.CreateUpdateDictModel):
    email: EmailStr
    password: str


class RecipeIngridientGetter(GetterDict):
    def get(self, key: str, default):
        if key == 'ingredients':
            return [
                association.ingredient.name
                for association in self._obj.ingredients
            ]
        return super().get(key, default)


class RecipeListResponse(BaseModel):
    id: int
    name: str
    description: str
    ingredients: list[str]
    duration: timedelta
    rating: float
    
    class Config:
        orm_mode = True
        getter_dict = RecipeIngridientGetter
    
    @classmethod
    def from_orm(cls, obj: tuple[Any, timedelta, float]):
        obj[0].duration = obj[1]
        obj[0].rating = obj[2]
        return super().from_orm(obj[0])


class RecipeStep(BaseModel):
    order: int
    description: str
    duration: timedelta
    
    class Config:
        orm_mode = True


class RecipeEntityResponse(BaseModel):
    id: int
    name: str
    description: str
    ingredients: list[str]
    steps: list[RecipeStep]
    
    class Config:
        orm_mode = True
        getter_dict = RecipeIngridientGetter


class FullRecipeData(BaseModel):
    name: str
    description: str
    ingredients: set[str]
    steps: list[RecipeStep]


class RateData(BaseModel):
    rate: int = Field(ge=0, le=5)
