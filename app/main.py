from fastapi import FastAPI
from fastapi_pagination import add_pagination
from sqlalchemy.exc import NoResultFound

from .api import router as api_router
from .config import settings
from .exception import InvalidImagesError
from .handler import image_upload_exception_handler, instance_not_found


app = FastAPI(debug=settings.DEBUG)
app.include_router(api_router)
app.add_exception_handler(
    InvalidImagesError,
    image_upload_exception_handler,
)
app.add_exception_handler(
    NoResultFound,
    instance_not_found,
)
add_pagination(app)
