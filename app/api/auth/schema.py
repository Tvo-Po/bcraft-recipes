from uuid import UUID

from fastapi_users import schemas
from pydantic import EmailStr


class UserRead(schemas.BaseUser[UUID]):
    pass


class UserCreate(schemas.CreateUpdateDictModel):
    email: EmailStr
    password: str
