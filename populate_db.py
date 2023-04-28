import asyncio
from datetime import timedelta
from random import choice, randint
from uuid import uuid4

from faker import Faker

from app.database.tools import async_session
from app.config import settings
from app.crud.image import create_images
from app.crud.recipe import create_recipe
from app.util import generate_image as gi


def generate_step(fake, step, images):
    return {
        'order': step,
        'description': fake.text(max_nb_chars=250),
        'duration': timedelta(seconds=randint(120, 5200)),
        'image_id': choice(images),
    }


def generate_image():
    id = uuid4()
    img = gi()
    with open(settings.MEDIA_PATH / f'{id.hex}.jpeg', 'wb') as img_file:
        img.save(img_file)
    return id


def generate_ingredient(fake):
    return ' '.join(fake.words(nb=randint(1, 3)))


def generate_recipe(fake, images):
    return {
        'name': ' '.join(fake.words(randint(1, 4))),
        'description': fake.text(max_nb_chars=250),
        'image_id': choice(images),
        'ingredients': set(generate_ingredient(fake) for _ in range(randint(2, 8))),
        'steps': [generate_step(fake, i, images) for i in range(1, randint(4, 7))],
    }


async def save_in_db(fake, images, recipes):
    async with async_session() as session:
        await create_images(
            [
                {
                    'id': i,
                    'path': (settings.MEDIA_PATH / f'{i.hex}.jpeg').as_posix(),
                    'original_filename': fake.word() + '.png',
                }
                for i in images
            ],
            session,
        )
        for r in recipes:
            await create_recipe(r, session)


def populate():
    fake = Faker()
    populated_images = [generate_image() for _ in range(10)]
    recipes = [generate_recipe(fake, populated_images) for _ in range(100)]
    asyncio.run(save_in_db(fake, populated_images, recipes))


if __name__ == '__main__':
    populate()
