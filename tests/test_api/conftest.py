from httpx import AsyncClient
import pytest

from app.main import app


@pytest.fixture(scope='session')
async def aclient():
    async with AsyncClient(app=app, base_url='http://test') as aclient:
        yield aclient
