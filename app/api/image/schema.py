from uuid import UUID

from pydantic import BaseModel


class CreateImage(BaseModel):
    id: UUID
    path: str
    original_filename: str | None


class StoredImage(BaseModel):
    id: UUID
    original_filename: str | None

    class Config:
        orm_mode = True
