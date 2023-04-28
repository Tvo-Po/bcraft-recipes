from fastapi.routing import APIRouter

from .auth.route import router as auth_router
from .image.route import router as image_router
from .recipe.route import router as recipe_router


router = APIRouter(prefix='/api/v1')

router.include_router(auth_router)
router.include_router(image_router)
router.include_router(recipe_router)
