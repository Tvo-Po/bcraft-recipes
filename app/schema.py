from pydantic import BaseModel
from pydantic.utils import GetterDict


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
    
    class Config:
        orm_mode = True
        getter_dict = RecipeIngridientGetter


class RecipeStep(BaseModel):
    order: int
    description: str
    
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
