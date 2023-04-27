from fastapi.routing import APIRouter

from .schema import UserCreate, UserRead
from app.auth import auth_backend, fastapi_users


router = APIRouter(prefix='/auth', tags=['auth'])
router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix='/jwt', tags=['auth']
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),  # type: ignore
)
