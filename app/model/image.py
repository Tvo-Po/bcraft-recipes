from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Image(Base):
    __tablename__ = 'image'

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    path: Mapped[str] = mapped_column(nullable=False)
    original_filename: Mapped[str] = mapped_column(nullable=True)
