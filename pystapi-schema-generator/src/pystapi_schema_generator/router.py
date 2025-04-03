import logging
from typing import Any

from fastapi import APIRouter, Path, Request
from stapi_fastapi.conformance import CORE
from stapi_fastapi.models.product import Product
from stapi_fastapi.responses import GeoJSONResponse
from stapi_pydantic import (
    Conformance,
    Order,
    OrderCollection,
    OrderStatus,
    OrderStatuses,
    ProductsCollection,
    RootResponse,
)

from .product_router import ProductRouter

logger = logging.getLogger(__name__)


class RootRouter(APIRouter):
    def __init__(
        self,
        conformances: list[str] = [CORE],
        name: str = "root",
        openapi_endpoint_name: str = "openapi",
        docs_endpoint_name: str = "swagger_ui_html",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.conformances = conformances
        self.name = name
        self.openapi_endpoint_name = openapi_endpoint_name
        self.docs_endpoint_name = docs_endpoint_name
        self.product_ids: list[str] = []

        # A dict is used to track the product routers so we can ensure
        # idempotentcy in case a product is added multiple times, and also to
        # manage clobbering if multiple products with the same product_id are
        # added.
        self.product_routers: dict[str, ProductRouter] = {}

        # Core endpoints
        self.add_api_route(
            "/",
            self.get_root,
            methods=["GET"],
            tags=["Core"],
            summary="landing page",
            description="...",
        )

        self.add_api_route(
            "/conformance",
            self.get_conformance,
            methods=["GET"],
            tags=["Core"],
            summary="information about specifications that this API conforms to",
            description="A list of all conformance classes specified in a standard that the server conforms to.",
        )

        # Orders endpoints - w/o specific {productId}/orders endpoints
        self.add_api_route(
            "/orders",
            self.get_orders,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Orders"],
            summary="a list of orders",
            description="...",
        )

        self.add_api_route(
            "/orders/{orderId}",
            self.get_order,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Orders"],
            summary="describe the order with id `orderId`",
            description="...",
        )

        self.add_api_route(
            "/orders/{orderId}/statuses",
            self.get_order_statuses,
            methods=["GET"],
            tags=["Orders"],
            summary="describe the statuses that the order with id `orderId` has had",
            description="...",
        )

        # Products endpoints
        self.add_api_route(
            "/products",
            self.get_products,
            methods=["GET"],
            tags=["Products"],
            summary="the products in the dataset",
            description="...",
        )

    def add_product(self, product: Product, *args: Any, **kwargs: Any) -> None:
        # Give the include a prefix from the product router
        product_router = ProductRouter(product, self, *args, **kwargs)
        self.include_router(product_router, prefix=f"/products/{product.id}")
        self.product_routers[product.id] = product_router
        self.product_ids = [*self.product_routers.keys()]

    def get_root(self, request: Request) -> RootResponse:
        return None  # type: ignore

    def get_conformance(self) -> Conformance:
        return None  # type: ignore

    def get_products(self, request: Request) -> ProductsCollection:
        return None  # type: ignore

    def get_orders(self, request: Request) -> OrderCollection[OrderStatus]:
        return None  # type: ignore

    def get_order(
        self,
        request: Request,
        order_id: str = Path(alias="orderId", description="local identifier of an order"),
    ) -> Order[OrderStatus]:
        return None  # type: ignore

    def get_order_statuses(
        self,
        order_id: str,
        request: Request,
        next: str | None = None,
        limit: int = 10,
    ) -> OrderStatuses:  # type: ignore
        return None  # type: ignore
