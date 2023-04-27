from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.image import Image


async def get_image_path(id: UUID, session: AsyncSession) -> str:
    return (
        await session.execute(select(Image).filter_by(id=id))
    ).scalars().one().path


async def create_images(
    images_data: list[dict[str, Any]],
    session: AsyncSession,
) -> list[Image]:
    images = [Image(**data) for data in images_data]
    session.add_all(images)
    await session.commit()
    return images
