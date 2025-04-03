from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from stapi_fastapi.models.product import Product
from stapi_fastapi.responses import GeoJSONResponse
from stapi_pydantic import (
    JsonSchemaModel,
    OpportunityCollection,
    OpportunityPayload,
    Order,
    OrderCollection,
    OrderPayload,
    OrderStatus,
    Prefer,
)

if TYPE_CHECKING:
    from stapi_fastapi.routers import RootRouter

logger = logging.getLogger(__name__)


def get_prefer(prefer: str | None = Header(None)) -> str | None:
    if prefer is None:
        return None

    if prefer not in Prefer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Prefer header value: {prefer}",
        )

    return Prefer(prefer)


class ProductRouter(APIRouter):
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

        # Product endpoints
        self.add_api_route(
            path="",
            endpoint=self.get_product,
            methods=["GET"],
            tags=["Products"],
            summary="describe the product with id `productId`",
            description="...",
        )

        self.add_api_route(
            path="/queryables",
            endpoint=self.get_product_queryables,
            methods=["GET"],
            tags=["Products"],
            summary="describe the queryables for a product",
            description="...",
        )

        self.add_api_route(
            path="/order-parameters",
            endpoint=self.get_product_order_parameters,
            methods=["GET"],
            tags=["Products"],
            summary="describe the order parameters for a product",
            description="...",
        )

        # Orders endpoints
        self.add_api_route(
            path="/orders",
            endpoint=self.create_order,
            methods=["POST"],
            response_class=GeoJSONResponse,
            status_code=status.HTTP_201_CREATED,
            tags=["Orders"],
            summary="create a new order for product with id `productId`",
            description="...",
        )

        self.add_api_route(
            path="/orders",
            endpoint=self.get_orders,
            methods=["GET"],
            response_class=GeoJSONResponse,
            tags=["Orders"],
            summary="get a list of orders for the specific product",
            description="...",
        )

        # Opportunities endpoints
        self.add_api_route(
            path="/opportunities",
            endpoint=self.search_opportunities,
            methods=["POST"],
            tags=["Opportunities"],
            summary="create a new opportunity request for product with id `productId`",
            description="...",
        )

    def get_product(self, request: Request) -> Product:
        return None  # type: ignore

    def get_product_queryables(self) -> JsonSchemaModel:
        return None  # type: ignore

    def get_product_order_parameters(self) -> JsonSchemaModel:
        return None  # type: ignore

    def create_order(self, payload: OrderPayload, request: Request, response: Response) -> Order:  # type: ignore
        return None  # type: ignore

    def get_orders(self, request: Request, next: str | None = None, limit: int = 10) -> OrderCollection[OrderStatus]:
        return None  # type: ignore

    def get_opportunity_collection(self, opportunity_collection_id: str, request: Request) -> OpportunityCollection:  # type: ignore
        return None  # type: ignore

    def search_opportunities(
        self,
        search: OpportunityPayload,
        request: Request,
        response: Response,
        prefer: Prefer | None,
    ) -> OpportunityCollection:  # type: ignore
        return None  # type: ignore
