from typing import Any

from fastapi import (
    APIRouter,
    Request,
)
from fastapi.datastructures import URL


class StapiFastapiBaseRouter(APIRouter):
    @staticmethod
    def url_for(request: Request, name: str, /, **path_params: Any) -> URL:
        return request.url_for(name, **path_params)
