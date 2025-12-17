import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.datastructures import URL
from returns.maybe import Maybe, Some
from returns.result import Failure, Success
from stapi_pydantic import (
    Conformance,
    Link,
    OpportunitySearchRecord,
    OpportunitySearchRecords,
    OpportunitySearchStatus,
    Order,
    OrderCollection,
    OrderStatus,
    OrderStatuses,
    ProductsCollection,
    RootResponse,
)

from stapi_fastapi.backends.root_backend import (
    GetOpportunitySearchRecord,
    GetOpportunitySearchRecords,
    GetOpportunitySearchRecordStatuses,
    GetOrder,
    GetOrders,
    GetOrderStatuses,
)
from stapi_fastapi.conformance import API as API_CONFORMANCE
from stapi_fastapi.constants import TYPE_GEOJSON
from stapi_fastapi.errors import NotFoundError
from stapi_fastapi.models.product import Product
from stapi_fastapi.responses import GeoJSONResponse
from stapi_fastapi.routers.base import StapiFastapiBaseRouter
from stapi_fastapi.routers.product_router import ProductRouter
from stapi_fastapi.routers.route_names import (
    CONFORMANCE,
    GET_OPPORTUNITY_SEARCH_RECORD,
    GET_OPPORTUNITY_SEARCH_RECORD_STATUSES,
    GET_ORDER,
    LIST_OPPORTUNITY_SEARCH_RECORDS,
    LIST_ORDER_STATUSES,
    LIST_ORDERS,
    LIST_PRODUCTS,
    ROOT,
)
from stapi_fastapi.routers.utils import json_link

logger = logging.getLogger(__name__)


class RootRouter(StapiFastapiBaseRouter):
    def __init__(
        self,
        get_orders: GetOrders,
        get_order: GetOrder,
        get_order_statuses: GetOrderStatuses | None = None,  # type: ignore
        get_opportunity_search_records: GetOpportunitySearchRecords | None = None,
        get_opportunity_search_record: GetOpportunitySearchRecord | None = None,
        get_opportunity_search_record_statuses: GetOpportunitySearchRecordStatuses | None = None,
        conformances: list[str] = [API_CONFORMANCE.core],
        name: str = "root",
        openapi_endpoint_name: str = "openapi",
        docs_endpoint_name: str = "swagger_ui_html",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        _conformances = set(conformances)

        self._get_orders = get_orders
        self._get_order = get_order
        self.__get_order_statuses = get_order_statuses
        self.__get_opportunity_search_records = get_opportunity_search_records
        self.__get_opportunity_search_record = get_opportunity_search_record
        self.__get_opportunity_search_record_statuses = get_opportunity_search_record_statuses
        self.name = name
        self.openapi_endpoint_name = openapi_endpoint_name
        self.docs_endpoint_name = docs_endpoint_name
        self.product_ids: list[str] = []

        # A dict is used to track the product routers so we can ensure
        # idempotentcy in case a product is added multiple times, and also to
        # manage clobbering if multiple products with the same product_id are
        # added.
        self.product_routers: dict[str, ProductRouter] = {}

        self.add_api_route(
            "/",
            self.get_root,
            methods=["GET"],
            name=f"{self.name}:{ROOT}",
            tags=["Root"],
        )

        self.add_api_route(
            "/conformance",
            self.get_conformance,
            methods=["GET"],
            name=f"{self.name}:{CONFORMANCE}",
            tags=["Conformance"],
        )

        self.add_api_route(
            "/products",
            self.get_products,
            methods=["GET"],
            name=f"{self.name}:{LIST_PRODUCTS}",
            tags=["Products"],
        )

        self.add_api_route(
            "/orders",
            self.get_orders,
            methods=["GET"],
            name=f"{self.name}:{LIST_ORDERS}",
            response_class=GeoJSONResponse,
            tags=["Orders"],
        )

        self.add_api_route(
            "/orders/{order_id}",
            self.get_order,
            methods=["GET"],
            name=f"{self.name}:{GET_ORDER}",
            response_class=GeoJSONResponse,
            tags=["Orders"],
        )

        if self.get_order_statuses is not None:
            _conformances.add(API_CONFORMANCE.order_statuses)
            self.add_api_route(
                "/orders/{order_id}/statuses",
                self.get_order_statuses,
                methods=["GET"],
                name=f"{self.name}:{LIST_ORDER_STATUSES}",
                tags=["Orders"],
            )

        if self.supports_async_opportunity_search:
            _conformances.add(API_CONFORMANCE.searches_opportunity)
            self.add_api_route(
                "/searches/opportunities",
                self.get_opportunity_search_records,
                methods=["GET"],
                name=f"{self.name}:{LIST_OPPORTUNITY_SEARCH_RECORDS}",
                summary="List all Opportunity Search Records",
                tags=["Opportunities"],
            )

            self.add_api_route(
                "/searches/opportunities/{search_record_id}",
                self.get_opportunity_search_record,
                methods=["GET"],
                name=f"{self.name}:{GET_OPPORTUNITY_SEARCH_RECORD}",
                summary="Get an Opportunity Search Record by ID",
                tags=["Opportunities"],
            )

        if self.__get_opportunity_search_record_statuses is not None:
            _conformances.add(API_CONFORMANCE.searches_opportunity_statuses)
            self.add_api_route(
                "/searches/opportunities/{search_record_id}/statuses",
                self.get_opportunity_search_record_statuses,
                methods=["GET"],
                name=f"{self.name}:{GET_OPPORTUNITY_SEARCH_RECORD_STATUSES}",
                summary="Get an Opportunity Search Record statuses by ID",
                tags=["Opportunities"],
            )

        self.conformances = list(_conformances)

    def get_root(self, request: Request) -> RootResponse:
        links = [
            json_link(
                "self",
                self.url_for(request, f"{self.name}:{ROOT}"),
            ),
            json_link(
                "service-description",
                self.url_for(request, self.openapi_endpoint_name),
            ),
            Link(
                rel="service-docs",
                href=self.url_for(request, self.docs_endpoint_name),
                type="text/html",
            ),
            json_link("conformance", href=self.url_for(request, f"{self.name}:{CONFORMANCE}")),
            json_link("products", self.url_for(request, f"{self.name}:{LIST_PRODUCTS}")),
            Link(
                rel="orders",
                href=self.url_for(request, f"{self.name}:{LIST_ORDERS}"),
                type=TYPE_GEOJSON,
            ),
        ]

        if self.supports_async_opportunity_search:
            links.append(
                json_link(
                    "opportunity-search-records",
                    self.url_for(request, f"{self.name}:{LIST_OPPORTUNITY_SEARCH_RECORDS}"),
                ),
            )

        return RootResponse(
            id="STAPI API",
            conformsTo=self.conformances,
            links=links,
        )

    def get_conformance(self) -> Conformance:
        return Conformance(conforms_to=self.conformances)

    def get_products(self, request: Request, next: str | None = None, limit: int = 10) -> ProductsCollection:
        start = 0
        limit = min(limit, 100)
        try:
            if next:
                start = self.product_ids.index(next)
        except ValueError:
            logger.exception("An error occurred while retrieving products")
            raise NotFoundError(detail="Error finding pagination token for products") from None
        end = start + limit
        ids = self.product_ids[start:end]
        links = [
            json_link(
                "self",
                self.url_for(request, f"{self.name}:{LIST_PRODUCTS}"),
            ),
        ]
        if end > 0 and end < len(self.product_ids):
            links.append(self.pagination_link(request, f"{self.name}:{LIST_PRODUCTS}", self.product_ids[end], limit))
        return ProductsCollection(
            products=[self.product_routers[product_id].get_product(request) for product_id in ids],
            links=links,
        )

    async def get_orders(  # noqa: C901
        self, request: Request, next: str | None = None, limit: int = 10
    ) -> OrderCollection[OrderStatus]:
        links: list[Link] = []
        orders_count: int | None = None
        match await self._get_orders(next, limit, request):
            case Success((orders, maybe_pagination_token, maybe_orders_count)):
                for order in orders:
                    order.links.extend(self.order_links(order, request))
                match maybe_pagination_token:
                    case Some(next_):
                        links.append(self.pagination_link(request, f"{self.name}:{LIST_ORDERS}", next_, limit))
                    case Maybe.empty:
                        pass
                match maybe_orders_count:
                    case Some(x):
                        orders_count = x
                    case Maybe.empty:
                        pass
            case Failure(ValueError()):
                raise NotFoundError(detail="Error finding pagination token")
            case Failure(e):
                logger.error(
                    "An error occurred while retrieving orders: %s",
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error finding Orders",
                )
            case _:
                raise AssertionError("Expected code to be unreachable")

        return OrderCollection(
            features=orders,
            links=links,
            number_matched=orders_count,
        )

    async def get_order(self, order_id: str, request: Request) -> Order[OrderStatus]:
        """
        Get details for order with `order_id`.
        """
        match await self._get_order(order_id, request):
            case Success(Some(order)):
                order.links.extend(self.order_links(order, request))
                return order  # type: ignore
            case Success(Maybe.empty):
                raise NotFoundError("Order not found")
            case Failure(e):
                logger.error(
                    "An error occurred while retrieving order '%s': %s",
                    order_id,
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error finding Order",
                )
            case _:
                raise AssertionError("Expected code to be unreachable")

    async def get_order_statuses(
        self,
        order_id: str,
        request: Request,
        next: str | None = None,
        limit: int = 10,
    ) -> OrderStatuses:  # type: ignore
        links: list[Link] = []
        match await self._get_order_statuses(order_id, next, limit, request):
            case Success(Some((statuses, maybe_pagination_token))):
                links.append(self.order_statuses_link(request, order_id))
                match maybe_pagination_token:
                    case Some(next_):
                        links.append(
                            self.pagination_link(
                                request, f"{self.name}:{LIST_ORDER_STATUSES}", next_, limit, order_id=order_id
                            )
                        )
                    case Maybe.empty:
                        pass
            case Success(Maybe.empty):
                raise NotFoundError("Order not found")
            case Failure(ValueError()):
                raise NotFoundError("Error finding pagination token")
            case Failure(e):
                logger.error(
                    "An error occurred while retrieving order statuses: %s",
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error finding Order Statuses",
                )
            case _:
                raise AssertionError("Expected code to be unreachable")
        return OrderStatuses(statuses=statuses, links=links)

    def add_product(self, product: Product, *args: Any, **kwargs: Any) -> None:
        # Give the include a prefix from the product router
        product_router = ProductRouter(product, self, *args, **kwargs)
        self.include_router(product_router, prefix=f"/products/{product.id}")
        self.product_routers[product.id] = product_router
        self.product_ids = [*self.product_routers.keys()]

    def generate_order_href(self, request: Request, order_id: str) -> URL:
        return self.url_for(request, f"{self.name}:{GET_ORDER}", order_id=order_id)

    def generate_order_statuses_href(self, request: Request, order_id: str) -> URL:
        return self.url_for(request, f"{self.name}:{LIST_ORDER_STATUSES}", order_id=order_id)

    def order_links(self, order: Order[OrderStatus], request: Request) -> list[Link]:
        return [
            Link(
                href=self.generate_order_href(request, order.id),
                rel="self",
                type=TYPE_GEOJSON,
            ),
            json_link(
                "monitor",
                self.generate_order_statuses_href(request, order.id),
            ),
        ]

    def order_statuses_link(self, request: Request, order_id: str) -> Link:
        return json_link("self", self.url_for(request, f"{self.name}:{LIST_ORDER_STATUSES}", order_id=order_id))

    def pagination_link(self, request: Request, name: str, pagination_token: str, limit: int, **kwargs: Any) -> Link:
        return json_link(
            "next",
            self.url_for(request, name, **kwargs).include_query_params(next=pagination_token, limit=limit),
        )

    async def get_opportunity_search_records(
        self, request: Request, next: str | None = None, limit: int = 10
    ) -> OpportunitySearchRecords:
        links: list[Link] = []
        match await self._get_opportunity_search_records(next, limit, request):
            case Success((records, maybe_pagination_token)):
                for record in records:
                    record.links.append(self.opportunity_search_record_self_link(record, request))
                match maybe_pagination_token:
                    case Some(next_):
                        links.append(
                            self.pagination_link(
                                request, f"{self.name}:{LIST_OPPORTUNITY_SEARCH_RECORDS}", next_, limit
                            )
                        )
                    case Maybe.empty:
                        pass
            case Failure(ValueError()):
                raise NotFoundError(detail="Error finding pagination token")
            case Failure(e):
                logger.error(
                    "An error occurred while retrieving opportunity search records: %s",
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error finding Opportunity Search Records",
                )
            case _:
                raise AssertionError("Expected code to be unreachable")
        return OpportunitySearchRecords(search_records=records, links=links)

    async def get_opportunity_search_record(self, search_record_id: str, request: Request) -> OpportunitySearchRecord:
        """
        Get the Opportunity Search Record with `search_record_id`.
        """
        match await self._get_opportunity_search_record(search_record_id, request):
            case Success(Some(search_record)):
                search_record.links.append(self.opportunity_search_record_self_link(search_record, request))
                return search_record  # type: ignore
            case Success(Maybe.empty):
                raise NotFoundError("Opportunity Search Record not found")
            case Failure(e):
                logger.error(
                    "An error occurred while retrieving opportunity search record '%s': %s",
                    search_record_id,
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error finding Opportunity Search Record",
                )
            case _:
                raise AssertionError("Expected code to be unreachable")

    async def get_opportunity_search_record_statuses(
        self, search_record_id: str, request: Request
    ) -> list[OpportunitySearchStatus]:
        """
        Get the Opportunity Search Record statuses with `search_record_id`.
        """
        match await self._get_opportunity_search_record_statuses(search_record_id, request):
            case Success(Some(search_record_statuses)):
                return search_record_statuses  # type: ignore
            case Success(Maybe.empty):
                raise NotFoundError("Opportunity Search Record not found")
            case Failure(e):
                logger.error(
                    "An error occurred while retrieving opportunity search record statuses '%s': %s",
                    search_record_id,
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error finding Opportunity Search Record statuses",
                )
            case _:
                raise AssertionError("Expected code to be unreachable")

    def generate_opportunity_search_record_href(self, request: Request, search_record_id: str) -> URL:
        return self.url_for(
            request,
            f"{self.name}:{GET_OPPORTUNITY_SEARCH_RECORD}",
            search_record_id=search_record_id,
        )

    def opportunity_search_record_self_link(
        self, opportunity_search_record: OpportunitySearchRecord, request: Request
    ) -> Link:
        return json_link("self", self.generate_opportunity_search_record_href(request, opportunity_search_record.id))

    @property
    def _get_order_statuses(self) -> GetOrderStatuses:  # type: ignore
        if not self.__get_order_statuses:
            raise AttributeError("Root router does not support order status history")
        return self.__get_order_statuses

    @property
    def _get_opportunity_search_records(self) -> GetOpportunitySearchRecords:
        if not self.__get_opportunity_search_records:
            raise AttributeError("Root router does not support async opportunity search")
        return self.__get_opportunity_search_records

    @property
    def _get_opportunity_search_record(self) -> GetOpportunitySearchRecord:
        if not self.__get_opportunity_search_record:
            raise AttributeError("Root router does not support async opportunity search")
        return self.__get_opportunity_search_record

    @property
    def _get_opportunity_search_record_statuses(self) -> GetOpportunitySearchRecordStatuses:
        if not self.__get_opportunity_search_record_statuses:
            raise AttributeError("Root router does not support async opportunity search status history")
        return self.__get_opportunity_search_record_statuses

    @property
    def supports_async_opportunity_search(self) -> bool:
        return self.__get_opportunity_search_records is not None and self.__get_opportunity_search_record is not None
