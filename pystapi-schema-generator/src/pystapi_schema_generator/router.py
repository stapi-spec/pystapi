from typing import Any

from fastapi import APIRouter, Path
from stapi_fastapi.responses import GeoJSONResponse
from stapi_pydantic import (
    Conformance,
    Order,
    OrderCollection,
    OrderStatus,
    OrderStatuses,
    Product,
    ProductsCollection,
    RootResponse,
)

from .product_router import ProductRouter


class RootRouter(APIRouter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.product_routers: dict[str, ProductRouter] = {}

        # Core endpoints
        self.add_api_route(
            "/",
            self.get_root,
            methods=["GET"],
            tags=["Core"],
            summary="STAPI root endpoint for API discovery and metadata",
            description=(
                "This endpoint serves as the entry point for API discovery and navigation. "
                "Returns the STAPI root endpoint response containing the API's metadata: "
                "a unique identifier, descriptive text, implemented conformance classes, "
                "and hypermedia links to available resources and documentation."
            ),
        )

        self.add_api_route(
            "/conformance",
            self.get_conformance,
            methods=["GET"],
            tags=["Core"],
            summary="List of implemented STAPI and OGC conformance classes",
            description=(
                "Returns a list of conformance classes implemented by this API, following "
                "the OGC API Features conformance structure. While the core STAPI "
                "conformance classes are already communicated in the root endpoint, "
                "OGC API requires this duplicate conformance information at this "
                "/conformance endpoint. Includes both STAPI-specific conformance classes "
                "(e.g., core, order statuses, searches) and relevant OGC conformance classes."
            ),
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

    # Core endpoints
    def get_root(self) -> RootResponse:
        return None  # type: ignore

    def get_conformance(self) -> Conformance:
        return None  # type: ignore

    # Products endpoints
    def get_products(self) -> ProductsCollection:
        return None  # type: ignore

    def add_product(self, product: Product, *args: Any, **kwargs: Any) -> None:
        product_router = ProductRouter(product, self, *args, **kwargs)
        self.include_router(product_router, prefix=f"/products/{product.id}")
        self.product_routers[product.id] = product_router

    # Orders endpoints - w/o specific {productId}/orders endpoints
    def get_orders(self) -> OrderCollection[OrderStatus]:
        return None  # type: ignore

    def get_order(
        self, order_id: str = Path(alias="orderId", description="local identifier of an order")
    ) -> Order[OrderStatus]:
        return None  # type: ignore

    def get_order_statuses(self, order_id: str, next: str | None = None, limit: int = 10) -> OrderStatuses:  # type: ignore
        return None  # type: ignore
