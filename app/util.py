import io
from pathlib import Path
from random import choice, randint
from uuid import UUID

import aiofiles
from PIL import Image

from app.config import settings


async def save_image_to_media(
    image_id: UUID,
    inmemory_image: io.BytesIO,
    img_format: str | None = None,
) -> Path:
    print(settings)
    frmt = img_format if img_format is not None else 'JPEG'
    path = settings.MEDIA_PATH / f'{image_id.hex}.{frmt}'
    async with aiofiles.open(path, 'wb') as stored_file:
        await stored_file.write(inmemory_image.getvalue())
    return path


def generate_image():
    proportion = choice([(1, 2), (3, 4), (1, 1), (4, 3), (2, 1)])
    width = randint(380, 640)
    height = int(width / proportion[0] * proportion[1])
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    for x in range(width):
        for y in range(height):
            r = randint(0, 255)
            g = randint(0, 255)
            b = randint(0, 255)
            img.putpixel((x, y), value=(r, g, b))
    return img
