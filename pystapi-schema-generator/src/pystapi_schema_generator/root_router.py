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

from pystapi_schema_generator import STAPI_BASE_URL, STAPI_EXAMPLE_URL, STAPI_VERSION

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
            summary="API root",
            description=(
                "Returns the STAPI landing page with essential metadata about the API implementation. "
                "The response includes a unique identifier, descriptive text, and hypermedia links to "
                "related endpoints."
            ),
            response_model=RootResponse,
            response_description="STAPI landing page with API metadata and links",
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "stapi-example",
                                "title": "STAPI API",
                                "description": "Implementation of the STAPI specification for remote sensing data",
                                "conformsTo": [
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/core",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/order-statuses",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/opportunities",
                                ],
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/",
                                        "title": "STAPI API Root",
                                    },
                                    {
                                        "rel": "products",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/products",
                                        "title": "Available Products",
                                    },
                                    {
                                        "rel": "orders",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/orders",
                                        "title": "Order Management",
                                    },
                                    {
                                        "rel": "create-order",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/orders",
                                        "title": "Create Order",
                                    },
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
            summary="API conformance",
            description=(
                "Returns the list of conformance classes implemented by this API. While the core "
                "STAPI conformance classes are already communicated in the root endpoint, OGC API "
                "requires this duplicate conformance information at this endpoint."
            ),
            response_model=Conformance,
            response_description="List of implemented conformance classes",
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "conformsTo": [
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/core",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/order-statuses",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/opportunities",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/opportunities-async",
                                    "https://geojson.org/schema/Polygon.json",
                                    "https://geojson.org/schema/Point.json",
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
            summary="List products",
            description=(
                "Returns a collection of products offered by the provider. This endpoint helps "
                "users discover which queryables are available for each product."
            ),
            response_model=ProductsCollection,
            response_description="Collection of available products",
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "products": [
                                    {
                                        "type": "Collection",
                                        "stapi_type": "Product",
                                        "stapi_version": STAPI_VERSION,
                                        "id": "{productId}",
                                        "title": "Example Product",
                                        "description": "Example product for demonstration purposes",
                                        "license": "proprietary",
                                        "providers": [
                                            {
                                                "name": "Example Provider",
                                                "roles": ["producer"],
                                                "url": "https://example.com/provider",
                                                "description": "Example provider for demonstration purposes",
                                            },
                                            {
                                                "name": "Example Host",
                                                "roles": ["host"],
                                                "url": "https://example.com/host",
                                                "description": "Example host for demonstration purposes",
                                            },
                                        ],
                                        "conformsTo": [
                                            f"{STAPI_BASE_URL}/{STAPI_VERSION}/core",
                                            "https://geojson.org/schema/Polygon.json",
                                        ],
                                        "links": [
                                            {
                                                "rel": "self",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}",
                                            },
                                            {
                                                "rel": "queryables",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/queryables",
                                            },
                                            {
                                                "rel": "order-parameters",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/order-parameters",
                                            },
                                            {
                                                "rel": "conformance",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/conformance",
                                            },
                                        ],
                                    }
                                ],
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/products",
                                    }
                                ],
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
            summary="List orders",
            description=(
                "Returns a collection of orders in the system. "
                "The response includes pagination links for navigating through the collection."
            ),
            response_model=OrderCollection[OrderStatus],
            response_description="Collection of orders",
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "FeatureCollection",
                                "features": [
                                    {
                                        "type": "Feature",
                                        "id": "order-123",
                                        "properties": {
                                            "product_id": "{productId}",
                                            "created": "2024-01-01T00:00:00Z",
                                            "status": "accepted",
                                            "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                        },
                                        "geometry": {
                                            "type": "Polygon",
                                            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                        },
                                    }
                                ],
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/geo+json",
                                        "href": f"{STAPI_EXAMPLE_URL}/orders",
                                    }
                                ],
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
            summary="Get order",
            description=(
                "Returns detailed information about a specific order, including its status, parameters, and metadata."
            ),
            response_model=Order[OrderStatus],
            response_description="Order details",
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "Feature",
                                "id": "order-123",
                                "properties": {
                                    "product_id": "{productId}",
                                    "created": "2024-01-01T00:00:00Z",
                                    "status": "accepted",
                                    "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                    "order_parameters": {"format": "GeoTIFF", "processing_level": "L2A"},
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                },
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/geo+json",
                                        "href": f"{STAPI_EXAMPLE_URL}/orders/order-123",
                                    },
                                    {
                                        "rel": "monitor",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/orders/order-123/statuses",
                                    },
                                ],
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
            summary="Get order statuses",
            description=(
                "Returns the history of status changes for a specific order. The response includes "
                "pagination links for navigating through the status history."
            ),
            response_model=OrderStatuses[OrderStatus],
            response_description="Collection of order status updates",
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "statuses": [
                                    {
                                        "timestamp": "2024-01-01T00:00:00Z",
                                        "status_code": "received",
                                        "reason_text": "Order received and validated",
                                    },
                                    {
                                        "timestamp": "2024-01-01T00:05:00Z",
                                        "status_code": "accepted",
                                        "reason_text": "Order accepted for processing",
                                    },
                                    {
                                        "timestamp": "2024-01-02T00:00:00Z",
                                        "status_code": "completed",
                                        "reason_text": "Order completed successfully",
                                        "links": [
                                            {
                                                "rel": "delivery",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/deliveries/delivery-123",
                                            }
                                        ],
                                    },
                                ],
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/orders/order-123/statuses",
                                    }
                                ],
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Order not found"},
            },
        )

    def get_root(self) -> RootResponse:
        """Get the root endpoint response."""
        return None  # type: ignore

    def get_conformance(self) -> Conformance:
        """Get the conformance classes supported by this API."""
        return None  # type: ignore

    def get_products(self) -> ProductsCollection:
        """Get the list of available products."""
        return None  # type: ignore

    def add_product(self, product: Product, *args: Any, **kwargs: Any) -> None:
        """Add a product router to the root router."""
        self.product_routers[product.id] = ProductRouter(product, self, *args, **kwargs)
        self.include_router(self.product_routers[product.id], prefix=f"/products/{product.id}")

    def get_orders(
        self,
        next: str | None = Query(default=None, description="Token for pagination to the next page of results"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of orders to return per page"),
    ) -> OrderCollection[OrderStatus]:
        """Get the list of orders with pagination support."""
        return None  # type: ignore

    def get_order(
        self, order_id: str = Path(alias="orderId", description="Unique identifier of the order", example="order-123")
    ) -> Order[OrderStatus]:
        """Get details of a specific order."""
        return None  # type: ignore

    def get_order_statuses(
        self,
        order_id: str = Path(alias="orderId", description="Unique identifier of the order", example="order-123"),
        next: str | None = Query(default=None, description="Token for pagination to the next page of status history"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of status entries to return per page"),
    ) -> OrderStatuses[OrderStatus]:
        """Get the status history of a specific order."""
        return None  # type: ignore
