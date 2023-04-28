from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.auth import get_user_db
from app.api.auth import dependency


@pytest.mark.asyncio
async def test_current_user_dependency():
    user_db = await anext(get_user_db(Mock()))
    user = await dependency.get_authenticated_user(
        user_db.user_table(
            id=uuid4(),
            email='test@email.com',
            is_active=True,
        )
    )
    assert user.dict().keys() == {'id'}
    assert isinstance(user.dict()['id'], UUID)
