from typing import Any, ClassVar

from fastapi import APIRouter, Path, Query, status
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
    """Root router for STAPI endpoints."""

    product_routers: ClassVar[dict[str, ProductRouter]] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up all routes for the root router."""
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
            response_model=RootResponse,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "stapi-example",
                                "title": "STAPI API",
                                "description": "Implementation of the STAPI specification",
                                "conformsTo": [
                                    "https://stapi.example.com/v0.1.0/core",
                                    "https://stapi.example.com/v0.1.0/order-statuses",
                                ],
                                "links": [
                                    {"rel": "self", "type": "application/json", "href": "https://stapi.example.com/"}
                                ],
                            }
                        }
                    },
                }
            },
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
            response_model=Conformance,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "conformsTo": [
                                    "https://stapi.example.com/v0.1.0/core",
                                    "https://stapi.example.com/v0.1.0/order-statuses",
                                ]
                            }
                        }
                    },
                }
            },
        )

        # Products endpoints
        self.add_api_route(
            "/products",
            self.get_products,
            methods=["GET"],
            tags=["Products"],
            summary="List of available products from the provider",
            description=(
                "Returns a collection of products offered by the provider. Each product contains "
                "required fields (type, id, title, description, license, providers, links) and "
                "optional fields (keywords, queryables, parameters, properties). The parameters "
                "field defines what can be ordered for each product (e.g., cloud cover limits), "
                "while the properties field describes inherent characteristics of the product "
                "(e.g., sensor type, frequency band). The response is represented as a GeoJSON "
                "FeatureCollection and includes pagination links for navigating through the "
                "product collection."
            ),
            response_model=ProductsCollection,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "products": [
                                    {
                                        "type": "Product",
                                        "id": "multispectral",
                                        "title": "Multispectral",
                                        "description": "Full color EO image",
                                        "license": "proprietary",
                                        "links": [],
                                    }
                                ],
                                "links": [],
                            }
                        }
                    },
                }
            },
        )

        # Orders endpoints
        self.add_api_route(
            "/orders",
            self.get_orders,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Orders"],
            summary="List of orders in the system",
            description=(
                "Returns a collection of orders in the system. Each order contains required fields "
                "(datetime, geometry) and optional fields (queryables). The datetime field specifies "
                "the temporal extent of the order, while the geometry field defines its spatial extent. "
                "The queryables field contains the constraints specified for the order. The response is "
                "represented as a GeoJSON FeatureCollection and includes pagination links for navigating "
                "through the order collection."
            ),
            response_model=OrderCollection[OrderStatus],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "FeatureCollection",
                                "features": [],
                                "links": [],
                            }
                        }
                    },
                }
            },
        )

        self.add_api_route(
            "/orders/{orderId}",
            self.get_order,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Orders"],
            summary="Get details of a specific order",
            description=(
                "Returns detailed information about a specific order. The order contains required "
                "fields (datetime, geometry) defining its temporal and spatial extent, and optional "
                "fields (queryables) containing the order constraints. The response is represented as "
                "a GeoJSON Feature and may include additional metadata and links to related resources."
            ),
            response_model=Order[OrderStatus],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "Feature",
                                "id": "order-123",
                                "properties": {
                                    "product_id": "multispectral",
                                    "created": "2024-01-01T00:00:00Z",
                                    "status": "accepted",
                                },
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Order not found"},
            },
        )

        self.add_api_route(
            "/orders/{orderId}/statuses",
            self.get_order_statuses,
            methods=["GET"],
            tags=["Orders"],
            summary="Get status history of an order",
            description=(
                "Returns the history of status changes for a specific order. The response includes "
                "a chronological list of status updates, each containing the status value, timestamp, "
                "and any associated message or metadata. Supports pagination through the next and limit "
                "parameters to navigate through the status history."
            ),
            response_model=OrderStatuses[OrderStatus],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "statuses": [
                                    {
                                        "timestamp": "2024-01-01T00:00:00Z",
                                        "status_code": "accepted",
                                        "reason_text": "Order accepted for processing",
                                    }
                                ],
                                "links": [],
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Order not found"},
            },
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
        """Add a product router to the root router."""
        product_router = ProductRouter(product, self, *args, **kwargs)
        self.include_router(product_router, prefix=f"/products/{product.id}")
        self.product_routers[product.id] = product_router

    # Orders endpoints
    def get_orders(
        self,
        next: str | None = Query(default=None, description="Token for pagination to the next page of results"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of orders to return per page"),
    ) -> OrderCollection[OrderStatus]:
        return None  # type: ignore

    def get_order(
        self, order_id: str = Path(alias="orderId", description="Unique identifier of the order", example="order-123")
    ) -> Order[OrderStatus]:
        return None  # type: ignore

    def get_order_statuses(
        self,
        order_id: str = Path(alias="orderId", description="Unique identifier of the order", example="order-123"),
        next: str | None = Query(default=None, description="Token for pagination to the next page of status history"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of status entries to return per page"),
    ) -> OrderStatuses[OrderStatus]:
        return None  # type: ignore
