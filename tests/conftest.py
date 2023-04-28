import os
from pathlib import Path

from dotenv import load_dotenv


# Make switch app database to test_db for endpoint testing
load_dotenv(Path(__file__).parent.parent / '.env')
os.environ['DATABASE_URL'] = os.getenv('TEST_DATABASE_URL', '')


import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.config import settings


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session', autouse=True)
async def aengine():
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    if not database_exists(settings.TEST_CONNECTION_FOR_DB_LEVEL_DDL):
        create_database(settings.TEST_CONNECTION_FOR_DB_LEVEL_DDL)
    from app.database.base import Base
    from app.model import image, recipe, user

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    drop_database(settings.TEST_CONNECTION_FOR_DB_LEVEL_DDL)


@pytest.fixture(scope='session')
async def asession(aengine):
    async_session = sessionmaker(
        aengine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session
