import io
from pathlib import Path
from uuid import UUID

import aiofiles

from app.config import settings


async def save_image_to_media(
    image_id: UUID,
    inmemory_image: io.BytesIO,
    img_format: str | None = None,
) -> Path:
    frmt = img_format if img_format is not None else 'JPEG'
    path = settings.MEDIA_PATH / f'{image_id.hex}.{frmt}'
    async with aiofiles.open(path, 'wb') as stored_file:
        await stored_file.write(inmemory_image.getvalue())
    return path
