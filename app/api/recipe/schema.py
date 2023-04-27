from datetime import timedelta
from uuid import UUID

from pydantic import BaseModel, Field, validator
from pydantic.utils import GetterDict


class RecipeIngridientGetter(GetterDict):
    def get(self, key: str, default):
        if key == 'ingredients':
            return [
                association.ingredient.name
                for association in self._obj.ingredients
            ]
        return super().get(key, default)


class RecipeListAnnotationGetter(GetterDict):
    _MODEL = 0
    _DURATION = 1
    _RATING = 2
    
    def get(self, key: str, default):
        if key == 'ingredients':
            return [
                association.ingredient.name
                for association in self._obj[self._MODEL].ingredients
            ]
        if key == 'duration':
            return self._obj[self._DURATION]
        if key == 'rating':
            return self._obj[self._RATING]
        row = self._obj
        self._obj = row[self._MODEL]
        model_field = super().get(key, default)
        self._obj = row
        return model_field


class RecipeListResponse(BaseModel):
    id: int
    name: str
    description: str
    ingredients: list[str]
    duration: timedelta
    rating: float
    
    class Config:
        orm_mode = True
        getter_dict = RecipeListAnnotationGetter


class RecipeStep(BaseModel):
    order: int
    description: str
    duration: timedelta
    image_id: UUID
    
    class Config:
        orm_mode = True


class RecipeEntityResponse(BaseModel):
    id: int
    name: str
    description: str
    image_id: UUID
    ingredients: list[str]
    steps: list[RecipeStep]
    
    class Config:
        orm_mode = True
        getter_dict = RecipeIngridientGetter


class UploadRecipeStep(BaseModel):
    order: int
    description: str
    duration: timedelta
    image_id: UUID
    
    class Config:
        orm_mode = True
    
    @validator('duration')
    def validate_first_step(cls, duration: timedelta, values):
        if duration < timedelta(seconds=60):
            raise ValueError(
                "Duration must be at least 1m "
                f"not {duration.total_seconds()}s."
            )
        return duration


class FullRecipeData(BaseModel):
    name: str = Field(min_length=1)
    description: str
    image_id: UUID
    ingredients: set[str]
    steps: list[UploadRecipeStep]
    
    @validator('steps')
    def validate_first_step(cls, steps: list[UploadRecipeStep], values):
        if min(steps, key=lambda s: s.order).order != 1:
            raise ValueError("Steps order must starts from 1.")
        return steps
    
    @validator('steps')
    def validate_steps_sequence(cls, steps: list[UploadRecipeStep], values):
        steps_order = sorted(step.order for step in steps)
        if steps_order != list(range(min(steps_order), max(steps_order) + 1)):
            raise ValueError(
                "Steps order must form arithmetic progression "
                "with common difference equals 1. "
                "(example: [1, 2, 3, ..., 8, 9])"
            )
        return steps


class RateData(BaseModel):
    rate: int = Field(ge=1, le=5)
