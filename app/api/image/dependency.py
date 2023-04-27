import asyncio
import io
from typing import TypeAlias
from uuid import UUID, uuid4

from fastapi import File, UploadFile
from PIL import Image as PILImage, UnidentifiedImageError

from .schema import CreateImage, StoredImage
from app.exception import InvalidImagesError
from app.util import save_image_to_media


ValidImage: TypeAlias = tuple[UUID, io.BytesIO, str | None, str | None]


async def get_stored_images(files: list[UploadFile] = File()):
    valid_images: list[ValidImage] = []
    invalid_images: list[tuple[int, str | None]] = []
    for i, file in enumerate(files):
        binary_image = io.BytesIO()
        while content := await file.read(1024):
            binary_image.write(content)
        binary_image.seek(0)
        try:
            img = PILImage.open(binary_image)
            img.verify()
        except UnidentifiedImageError:
            invalid_images.append((i, file.filename))
        else:
            valid_images.append((
                uuid4(),
                binary_image,
                img.format,
                file.filename,
            ))
    if invalid_images:
        raise InvalidImagesError(invalid_images)
    paths = await asyncio.gather(*[
        save_image_to_media(id, bin_img, frmt)
        for id, bin_img, frmt, _ in valid_images
    ])
    return [
        CreateImage(
            id=id,
            path=path.as_posix(),
            original_filename=filename,
        ) for path, (id, _, _, filename) in zip(paths, valid_images)
    ]
