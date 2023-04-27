from fastapi import Depends

from app.auth import current_active_user
from .schema import AuthUser


async def get_authenticated_user(
    user = Depends(current_active_user)
) -> AuthUser:
    return AuthUser.from_orm(user)
