from uuid import UUID

from fastapi import Depends
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from .dependency import get_stored_images
from .schema import CreateImage, StoredImage
from app.database.tools import get_session
from app.crud import image as crud


router = APIRouter(prefix='/images', tags=['images'])


@router.post('/upload', response_model=list[StoredImage])
async def upload_images(
    images: list[CreateImage] = Depends(
        get_stored_images,
        use_cache=False,
    ),
    session: AsyncSession = Depends(get_session),
):
    await crud.create_images(
        [img.dict() for img in images],
        session
    )
    return images


@router.get('/{id}', response_class=FileResponse)
async def get_image(id: UUID, session: AsyncSession = Depends(get_session)):
    return await crud.get_image_path(id, session)
