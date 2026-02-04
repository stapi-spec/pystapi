from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import (
    APIRouter,
    Path,
    Query,
    Request,
    Response,
    status,
)
from geojson_pydantic import Polygon
from stapi_fastapi.responses import GeoJSONResponse
from stapi_pydantic import (
    Conformance,
    OpportunityCollection,
    OpportunityPayload,
    OpportunityProperties,
    Order,
    OrderCollection,
    OrderParameters,
    OrderPayload,
    OrderStatus,
    Prefer,
    Product,
    Queryables,
)

from pystapi_schema_generator import STAPI_BASE_URL, STAPI_EXAMPLE_URL, STAPI_VERSION

if TYPE_CHECKING:
    from .root_router import RootRouter


class ProductRouter(APIRouter):
    """Router for product-specific endpoints."""

    def __init__(
        self,
        product: Product,
        root_router: RootRouter,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.product = product
        self.root_router = root_router
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up all routes for the product router."""
        # Product endpoints
        self.add_api_route(
            path="",
            endpoint=self.get_product,
            methods=["GET"],
            tags=["Products"],
            summary="Get product",
            description=(
                "Returns detailed information about a specific product, including its metadata, "
                "capabilities, and configuration options."
            ),
            response_model=Product,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
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
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        self.add_api_route(
            path="/conformance",
            endpoint=self.get_conformance,
            methods=["GET"],
            tags=["Products"],
            summary="Get product conformance",
            description=(
                "Returns the conformance classes that apply specifically to this product, "
                "indicating which features and capabilities are supported."
            ),
            response_model=Conformance,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "conformsTo": [
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/core",
                                    "https://geojson.org/schema/Polygon.json",
                                    "https://geojson.org/schema/Point.json",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/opportunities",
                                    f"{STAPI_BASE_URL}/{STAPI_VERSION}/opportunities-async",
                                ]
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        self.add_api_route(
            path="/queryables",
            endpoint=self.get_queryables,
            methods=["GET"],
            tags=["Products"],
            summary="Get queryables",
            description=(
                "Returns a JSON Schema definition of the properties that can be used to filter "
                "opportunities and orders for this product."
            ),
            response_model=Queryables,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "type": "object",
                                "properties": {
                                    "eo:cloud_cover": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 100,
                                        "description": "Maximum cloud cover percentage",
                                    },
                                    "eo:resolution": {
                                        "type": "number",
                                        "minimum": 0,
                                        "description": "Minimum ground resolution in meters",
                                    },
                                    "datetime": {
                                        "type": "string",
                                        "format": "date-time",
                                        "description": "Acquisition time window",
                                    },
                                },
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        self.add_api_route(
            path="/order-parameters",
            endpoint=self.get_order_parameters,
            methods=["GET"],
            tags=["Products"],
            summary="Get order parameters",
            description=(
                "Returns a JSON Schema definition of the parameters that can be specified when "
                "creating an order for this product."
            ),
            response_model=OrderParameters,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "type": "object",
                                "properties": {
                                    "format": {
                                        "type": "string",
                                        "enum": ["GeoTIFF", "JPEG2000"],
                                        "description": "Output file format",
                                    },
                                    "processing_level": {
                                        "type": "string",
                                        "enum": ["L1C", "L2A"],
                                        "description": "Processing level",
                                    },
                                    "delivery_method": {
                                        "type": "string",
                                        "enum": ["download", "s3", "azure"],
                                        "description": "Delivery method",
                                    },
                                },
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        # Orders endpoints
        self.add_api_route(
            path="/orders",
            endpoint=self.create_order,
            methods=["POST"],
            response_class=GeoJSONResponse,
            status_code=status.HTTP_201_CREATED,
            tags=["Orders"],
            summary="Create order",
            description=(
                "Creates a new order for this product using the parameters defined in the product "
                "or provided through the opportunities endpoint."
            ),
            response_model=Order[OrderStatus],
            responses={
                status.HTTP_201_CREATED: {
                    "description": "Order created successfully",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "Feature",
                                "id": "order-123",
                                "properties": {
                                    "product_id": "{productId}",
                                    "created": "2024-01-01T00:00:00Z",
                                    "status": "received",
                                    "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                    "order_parameters": {
                                        "format": "GeoTIFF",
                                        "processing_level": "L2A",
                                        "delivery_method": "download",
                                    },
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
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid order request"},
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        self.add_api_route(
            path="/orders",
            endpoint=self.get_orders,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Orders"],
            summary="List product orders",
            description=(
                "Returns a collection of orders for this product. The response includes pagination "
                "links for navigating through the order collection."
            ),
            response_model=OrderCollection[OrderStatus],
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
                                            "order_parameters": {"format": "GeoTIFF", "processing_level": "L2A"},
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
                                        "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/orders",
                                    }
                                ],
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        # Opportunities endpoints
        self.add_api_route(
            path="/opportunities",
            endpoint=self.search_opportunities,
            methods=["POST"],
            response_class=GeoJSONResponse,
            tags=["Opportunities"],
            summary="Search opportunities",
            description=(
                "Explores the opportunities available for this product based on the provided "
                "parameters. Supports both synchronous and asynchronous search modes."
            ),
            response_model=OpportunityCollection[Polygon, OpportunityProperties],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful synchronous response",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "FeatureCollection",
                                "features": [
                                    {
                                        "type": "Feature",
                                        "id": "opp-123",
                                        "properties": {
                                            "product_id": "{productId}",
                                            "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                            "eo:cloud_cover": 10,
                                            "eo:resolution": 10,
                                        },
                                        "geometry": {
                                            "type": "Polygon",
                                            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                        },
                                        "links": [
                                            {
                                                "rel": "create-order",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/orders",
                                                "method": "POST",
                                                "body": {
                                                    "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                                    "geometry": {
                                                        "type": "Polygon",
                                                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                                    },
                                                },
                                            }
                                        ],
                                    }
                                ],
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/geo+json",
                                        "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/opportunities",
                                    }
                                ],
                            }
                        }
                    },
                },
                status.HTTP_201_CREATED: {
                    "description": "Asynchronous search initiated",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "search-123",
                                "product_id": "{productId}",
                                "request": {
                                    "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                    },
                                },
                                "status": {
                                    "timestamp": "2024-01-01T00:00:00Z",
                                    "status_code": "running",
                                    "reason_text": "Search in progress",
                                },
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/searches/opportunities/search-123",
                                    },
                                    {
                                        "rel": "monitor",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/searches/opportunities/search-123/statuses",
                                    },
                                ],
                            }
                        }
                    },
                },
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid search request"},
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        self.add_api_route(
            path="/opportunities/{opportunityCollectionId}",
            endpoint=self.get_opportunity_collection,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Opportunities"],
            summary="Get opportunity collection",
            description=(
                "Returns the opportunity collection for an asynchronous search. The response "
                "includes pagination links for navigating through the opportunity collection."
            ),
            response_model=OpportunityCollection[Polygon, OpportunityProperties],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/geo+json": {
                            "example": {
                                "type": "FeatureCollection",
                                "id": "opp-col-123",
                                "features": [
                                    {
                                        "type": "Feature",
                                        "id": "opp-123",
                                        "properties": {
                                            "product_id": "{productId}",
                                            "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                            "eo:cloud_cover": 10,
                                            "eo:resolution": 10,
                                        },
                                        "geometry": {
                                            "type": "Polygon",
                                            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                        },
                                        "links": [
                                            {
                                                "rel": "create-order",
                                                "type": "application/json",
                                                "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/orders",
                                                "method": "POST",
                                                "body": {
                                                    "datetime": "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
                                                    "geometry": {
                                                        "type": "Polygon",
                                                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                                                    },
                                                },
                                            }
                                        ],
                                    }
                                ],
                                "links": [
                                    {
                                        "rel": "self",
                                        "type": "application/geo+json",
                                        "href": f"{STAPI_EXAMPLE_URL}/products/{{productId}}/opportunities/opp-col-123",
                                    },
                                    {
                                        "rel": "search-record",
                                        "type": "application/json",
                                        "href": f"{STAPI_EXAMPLE_URL}/searches/opportunities/search-123",
                                    },
                                ],
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Opportunity collection not found"},
            },
        )

    def get_product(self) -> Product:
        """Get details of this product."""
        return None  # type: ignore

    def get_conformance(self) -> Conformance:
        """Get conformance classes for this product."""
        return None  # type: ignore

    def get_queryables(self) -> Queryables:
        """Get queryable properties for this product."""
        return None  # type: ignore

    def get_order_parameters(self) -> OrderParameters:
        """Get order parameters for this product."""
        return None  # type: ignore

    def create_order(
        self, payload: OrderPayload[OrderParameters], request: Request, response: Response
    ) -> Order[OrderStatus]:
        """Create a new order for this product."""
        return None  # type: ignore

    def get_orders(
        self,
        request: Request,
        next: str | None = Query(default=None, description="Token for pagination to the next page of results"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of orders to return per page"),
    ) -> OrderCollection[OrderStatus]:
        """Get orders for this product."""
        return None  # type: ignore

    def get_opportunity_collection(
        self,
        request: Request,
        opportunity_collection_id: str = Path(
            description="Unique identifier of the opportunity collection", example="opp-col-123"
        ),
    ) -> OpportunityCollection[Polygon, OpportunityProperties]:
        """Get opportunity collection for async search."""
        return None  # type: ignore

    def search_opportunities(
        self,
        search: OpportunityPayload,
        request: Request,
        response: Response,
        prefer: Prefer | None = Query(
            default=None, description="Preference for synchronous or asynchronous processing"
        ),
    ) -> OpportunityCollection[Polygon, OpportunityProperties]:
        """Search for acquisition opportunities."""
        return None  # type: ignore
