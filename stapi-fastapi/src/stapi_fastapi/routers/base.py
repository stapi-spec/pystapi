from typing import Any

from fastapi import (
    APIRouter,
    Request,
)
from fastapi.datastructures import URL


class StapiFastapiBaseRouter(APIRouter):
    #: Segments prefixed to the name of every route registered on this router,
    #: so route names stay unique across products.
    route_name_prefix: tuple[str, ...] = ()

    @staticmethod
    def url_for(request: Request, name: str, /, **path_params: Any) -> URL:
        return request.url_for(name, **path_params)

    def route_name(self, name: str) -> str:
        """The registered name of the route this router serves under `name`."""
        return ":".join((*self.route_name_prefix, name))
