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
            summary="Get details of a specific product",
            description=(
                "Returns detailed information about a specific product. The response includes "
                "all product metadata, including required fields (type, id, title, description, "
                "license, providers, links) and optional fields (keywords, queryables, parameters, "
                "properties). The parameters field defines what can be ordered for this product, "
                "while the properties field describes inherent characteristics of the product."
            ),
            response_model=Product,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "type": "Product",
                                "id": "multispectral",
                                "title": "Multispectral",
                                "description": "Full color EO image",
                                "license": "proprietary",
                                "providers": [
                                    {"name": "Example Provider", "roles": ["producer"], "url": "https://example.com"}
                                ],
                                "links": [],
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
            summary="Get conformance classes for a specific product",
            description=(
                "Returns the conformance classes that apply specifically to this product. "
                "These classes indicate which features and capabilities are supported by "
                "this product, such as supported geometry types, parameter types, and "
                "other product-specific capabilities."
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
                                    "https://geojson.org/schema/Polygon.json",
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
            summary="Get queryable properties for a specific product",
            description=(
                "Returns a JSON Schema definition of the properties that can be used to "
                "filter opportunities and orders for this product. These queryables define "
                "the constraints that can be applied when searching for or ordering this "
                "product, such as cloud cover limits, resolution requirements, or other "
                "product-specific parameters."
            ),
            response_model=Queryables,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "type": "object",
                                "properties": {"eo:cloud_cover": {"type": "number", "minimum": 0, "maximum": 100}},
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
            summary="Get order parameters for a specific product",
            description=(
                "Returns a JSON Schema definition of the parameters that can be specified "
                "when creating an order for this product. These parameters define the "
                "configurable options for the order, such as delivery format, processing "
                "level, or other product-specific options."
            ),
            response_model=OrderParameters,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "type": "object",
                                "properties": {"format": {"type": "string", "enum": ["GeoTIFF", "JPEG2000"]}},
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
            summary="Create a new order for a specific product",
            description=(
                "Creates a new order for this product. The request must include the required "
                "fields (datetime, geometry) and may include optional fields (queryables, "
                "order_parameters). The datetime field specifies the temporal extent of the "
                "order, while the geometry field defines its spatial extent. The response "
                "is a GeoJSON Feature representing the created order."
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
                                    "product_id": "multispectral",
                                    "created": "2024-01-01T00:00:00Z",
                                    "status": "received",
                                },
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
            summary="Get orders for a specific product",
            description=(
                "Returns a collection of orders for this product. Each order is a GeoJSON "
                "Feature containing the order details, including status, parameters, and "
                "metadata. The response is a GeoJSON FeatureCollection and includes "
                "pagination links for navigating through the order collection."
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
                },
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        # Opportunities endpoints
        self.add_api_route(
            path="/opportunities",
            endpoint=self.search_opportunities,
            methods=["POST"],
            tags=["Opportunities"],
            summary="Search for opportunities for a specific product",
            description=(
                "Searches for potential acquisition opportunities for this product based on "
                "the provided search criteria. The request must include the required fields "
                "(datetime, geometry) and may include optional fields (queryables). The "
                "response is a collection of opportunities that match the search criteria, "
                "each representing a potential acquisition that could fulfill an order."
            ),
            response_model=OpportunityCollection,
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "opportunities": [],
                                "links": [],
                            }
                        }
                    },
                },
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid search request"},
                status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
            },
        )

        self.add_api_route(
            path="/opportunities/{opportunity_collection_id}",
            endpoint=self.get_opportunity_collection,
            methods=["GET"],
            tags=["Opportunities"],
            summary="Get details of a specific opportunity collection",
            description=(
                "Returns detailed information about a specific opportunity collection. The response "
                "includes all opportunities in the collection, their properties, and any associated "
                "metadata. This endpoint is used to retrieve the results of an asynchronous "
                "opportunity search."
            ),
            response_model=OpportunityCollection[Polygon, OpportunityProperties],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "example": {
                                "opportunities": [],
                                "links": [],
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {"description": "Opportunity collection not found"},
            },
        )

    # Product endpoints
    def get_product(self) -> Product:
        return None  # type: ignore

    def get_conformance(self) -> Conformance:
        return None  # type: ignore

    def get_queryables(self) -> Queryables:
        return None  # type: ignore

    def get_order_parameters(self) -> OrderParameters:
        return None  # type: ignore

    # Orders endpoints
    def create_order(
        self, payload: OrderPayload[OrderParameters], request: Request, response: Response
    ) -> Order[OrderStatus]:
        return None  # type: ignore

    def get_orders(
        self,
        request: Request,
        next: str | None = Query(default=None, description="Token for pagination to the next page of results"),
        limit: int = Query(default=10, ge=1, le=100, description="Maximum number of orders to return per page"),
    ) -> OrderCollection[OrderStatus]:
        return None  # type: ignore

    def get_opportunity_collection(
        self,
        request: Request,
        opportunity_collection_id: str = Path(
            description="Unique identifier of the opportunity collection", example="opp-col-123"
        ),
    ) -> OpportunityCollection[Polygon, OpportunityProperties]:
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
        return None  # type: ignore
