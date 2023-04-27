from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from .exception import InvalidImagesError


async def instance_not_found(request: Request, exc: NoResultFound):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'detail': 'Not Found'}
    )

async def image_upload_exception_handler(request: Request, exc: InvalidImagesError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            'detail': [
                {
                    'loc': ['body', pos],
                    'msg': f"<{filename if filename else 'unnamed'}>"
                            " is not a valid image",
                    'type': 'type_error.image',
                } for pos, filename in exc.info
            ]
        },
    )
