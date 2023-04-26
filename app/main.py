from fastapi import FastAPI
from fastapi_pagination import add_pagination

from .config import settings
from .router import router


app = FastAPI(debug=settings.DEBUG)
app.include_router(router)

add_pagination(app)
