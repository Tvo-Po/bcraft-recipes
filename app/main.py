import asyncio
import io
from uuid import UUID, uuid4

import aiofiles
from fastapi import Depends, FastAPI, File, Request, status, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi_pagination import add_pagination
from PIL import Image as PILImage, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db import get_session
from .config import settings
from .model import Image
from .router import router
from .schema import StoredImage


app = FastAPI(debug=settings.DEBUG)
app.include_router(router)


class InvalidImagesError(Exception):
    def __init__(self, info: list[tuple[int, str | None]]) -> None:
        self.info = info
        string_errors = [
            f'\t{pos}: {name if name else "unnamed"}\n'
            for pos, name in info
        ]
        super().__init__(
            f"Invalid images (\n{''.join(string_errors)})"
        )


@app.exception_handler(InvalidImagesError)
async def image_upload_exception_handler(request: Request, exc: InvalidImagesError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            'detail': [
                {
                    'loc': ['body', pos],
                    'msg': f"<{filename if filename else 'unnamed'}>"
                            " is not a valid image",
                    'type': 'type_error.image',
                } for pos, filename in exc.info
            ]
        },
    )


async def save_image(
    inmemory_image: io.BytesIO,
    session: AsyncSession,
    img_format: str | None = None,
    original_filename: str | None = None,
):
    image_id = uuid4()
    frmt = img_format if img_format is not None else 'JPEG'
    path = settings.MEDIA_PATH / f'{image_id.hex}.{frmt}'
    async with aiofiles.open(path, 'wb') as stored_file:
        await stored_file.write(inmemory_image.getvalue())
    image_instance = Image(
        id=image_id,
        path=path.as_posix(),
        original_filename=original_filename,
    )
    session.add(image_instance)
    return image_instance


async def process_images(
    files: list[UploadFile] = File(),
    session: AsyncSession = Depends(get_session)
):
    valid_images = []
    invalid_images = []
    for i, file in enumerate(files):
        try:
            binary_image = io.BytesIO(await file.read())
            img = PILImage.open(binary_image)
            img.verify()
            valid_images.append((
                binary_image,
                img.format,
                file.filename,
            ))
        except UnidentifiedImageError:
            invalid_images.append((i, file.filename))
    if invalid_images:
        raise InvalidImagesError(invalid_images)
    saved_images_in_session = await asyncio.gather(
        *[
            save_image(img, session, frmt, filename)
            for img, frmt, filename in valid_images
        ]
    )
    await session.commit()
    return saved_images_in_session


@app.post('/upload/images', response_model=list[StoredImage])
async def upload_images(images: tuple[Image] = Depends(process_images)):
    return [StoredImage.from_orm(img) for img in images]


@app.get('/images/{id}', response_class=FileResponse)
async def get_image(id: UUID, session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(Image).filter_by(id=id))).scalars().one().path


add_pagination(app)
