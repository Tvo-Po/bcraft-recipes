from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserRead(schemas.BaseUser[UUID]):
    pass


class UserCreate(schemas.CreateUpdateDictModel):
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    id: UUID

    class Config:
        orm_mode = True
