from fastapi import FastAPI

from .config import settings
from .router import router


app = FastAPI(debug=settings.DEBUG)
app.include_router(router)
