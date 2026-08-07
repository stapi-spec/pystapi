import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from fastapi import (
    APIRouter,
    Request,
    Response,
    status,
)
from fastapi.datastructures import URL, Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from stapi_pydantic import Link

from stapi_fastapi.constants import TYPE_JSON
from stapi_fastapi.pagination import Page
from stapi_fastapi.routers.route_names import Tag

#: OpenAPI response declarations, keyed by status code.
Responses: TypeAlias = dict[int | str, dict[str, Any]]

# The error responses a route can declare, one apiece so a route composes only
# the ones it actually produces: `errors=NOT_FOUND | SERVER_ERROR`.

BAD_REQUEST: Responses = {
    status.HTTP_400_BAD_REQUEST: {
        "description": (
            "The request was rejected: e.g. it omits a predicate for a queryable the "
            "Product requires, or its `Prefer` header carries an unsupported value."
        ),
    },
}

NOT_FOUND: Responses = {
    status.HTTP_404_NOT_FOUND: {
        "description": (
            "The requested resource does not exist or is not accessible, or the "
            "supplied pagination token does not identify a page."
        ),
    },
}

SERVER_ERROR: Responses = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": ("The request could not be served because a backend reported failure."),
    },
}


_NON_IDENTIFIER = re.compile(r"\W")


def operation_id(route_name: str) -> str:
    """The published operationId for the route registered under `route_name`.

    Derived from the *prefixed* name, not from `Route.name`: a server mounting
    several products registers `get-product` once per product, and an
    operationId has to be unique across the whole document.
    """
    return _NON_IDENTIFIER.sub("_", route_name)


@dataclass(frozen=True, kw_only=True)
class Route:
    """One route of the STAPI contract, declared rather than hand-assembled."""

    name: str
    """The route family, one of the `stapi_fastapi.routers.route_names` constants.

    Prefixed with the owning router's segments to form the registered route name.
    """

    path: str
    endpoint: Callable[..., Any]

    summary: str
    """Required: it is the operation's title wherever the API is published."""

    tag: Tag
    """The OpenAPI tag this operation is published under."""

    methods: tuple[str, ...] = ("GET",)
    status_code: int | None = None
    # FastAPI's own defaults, as factories because a DefaultPlaceholder is
    # unhashable and so cannot be a dataclass default. They must stay the
    # placeholders: an explicit `None` response_model would suppress the
    # inference from the endpoint's return annotation.
    response_class: type[Response] | DefaultPlaceholder = field(default_factory=lambda: Default(JSONResponse))
    response_model: Any = field(default_factory=lambda: Default(None))
    responses: Responses = field(default_factory=dict)
    """Responses particular to this route, merged over `errors`."""

    errors: Responses
    """The error responses this route can actually produce, e.g.
    `NOT_FOUND | SERVER_ERROR`, or `{}` for a route that produces none.
    """

    def to_api_route(self, name: str) -> dict[str, Any]:
        """This route as keyword arguments for `APIRouter.add_api_route`.

        `name` is the registered name, passed in rather than derived, so
        `StapiFastapiBaseRouter.route_name` stays the only place that knows how a
        prefixed route name is spelled.
        """
        return {
            "path": self.path,
            "endpoint": self.endpoint,
            "name": name,
            "operation_id": operation_id(name),
            "tags": [self.tag],
            "summary": self.summary,
            "methods": list(self.methods),
            "status_code": self.status_code,
            "response_class": self.response_class,
            "response_model": self.response_model,
            "responses": {**self.errors, **self.responses},
        }


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

    def self_link(self, request: Request, name: str, **path_params: Any) -> Link:
        """A `self` link for the current request."""
        return Link(href=self.url_for(request, name, **path_params), rel="self", type=TYPE_JSON)

    def pagination_link(self, request: Request, name: str, pagination_token: str, limit: int, **kwargs: Any) -> Link:
        """A `next` link for the page after the one being returned."""
        url = self.url_for(request, name, **kwargs).include_query_params(next=pagination_token, limit=limit)
        return Link(href=url, rel="next", type=TYPE_JSON)

    def page_links(
        self,
        request: Request,
        page: Page[Any],
        name: str,
        limit: int,
        **path_params: Any,
    ) -> list[Link]:
        """The links published on a collection response for `page`.

        Backend-supplied links come first: they describe the collection rather
        than this page of it.
        """
        links = [*page.links, self.self_link(request, name, **path_params)]
        next_token = page.next_token.value_or(None)
        if next_token is not None:
            links.append(self.pagination_link(request, name, next_token, limit, **path_params))
        return links

    def register_route(self, route: Route) -> None:
        """Register `route` on this router."""
        self.add_api_route(**route.to_api_route(self.route_name(route.name)))
