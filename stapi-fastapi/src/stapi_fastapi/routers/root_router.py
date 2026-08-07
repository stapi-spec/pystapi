import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.datastructures import URL
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, Success
from stapi_pydantic import (
    Conformance,
    Link,
    OpportunitySearchRecord,
    OpportunitySearchRecordCollection,
    OpportunitySearchStatusCollection,
    Order,
    OrderCollection,
    OrderStatus,
    OrderStatusCollection,
    ProductCollection,
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
from stapi_fastapi.errors import NotFoundError, PaginationTokenError
from stapi_fastapi.models.product import Product
from stapi_fastapi.pagination import Page
from stapi_fastapi.path_params import OrderIdPath, SearchRecordIdPath
from stapi_fastapi.query_params import DEFAULT_LIMIT, Limit, NextToken
from stapi_fastapi.responses import GeoJSONResponse
from stapi_fastapi.routers.base import NOT_FOUND, SERVER_ERROR, Route, StapiFastapiBaseRouter
from stapi_fastapi.routers.product_router import ProductRouter
from stapi_fastapi.routers.route_names import (
    CONFORMANCE,
    GET_OPPORTUNITY_SEARCH_RECORD,
    GET_ORDER,
    LIST_OPPORTUNITY_SEARCH_RECORD_STATUSES,
    LIST_OPPORTUNITY_SEARCH_RECORDS,
    LIST_ORDER_STATUSES,
    LIST_ORDERS,
    LIST_PRODUCTS,
    ROOT,
    Tag,
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
        conformances: list[str] | None = None,
        name: str = "root",
        openapi_endpoint_name: str = "openapi",
        docs_endpoint_name: str = "swagger_ui_html",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        # The optional conformance classes are derived from the backends actually
        # supplied and re-added below alongside their routes: advertising a class
        # whose routes were never registered would send clients to a 404.
        _conformances = set(conformances or [API_CONFORMANCE.core]) - {
            API_CONFORMANCE.order_statuses,
            API_CONFORMANCE.searches_opportunity,
            API_CONFORMANCE.searches_opportunity_statuses,
        }

        self._get_orders = get_orders
        self._get_order = get_order
        self.__get_order_statuses = get_order_statuses
        self.__get_opportunity_search_records = get_opportunity_search_records
        self.__get_opportunity_search_record = get_opportunity_search_record
        self.__get_opportunity_search_record_statuses = get_opportunity_search_record_statuses
        self.name = name
        self.route_name_prefix = (name,)
        self.openapi_endpoint_name = openapi_endpoint_name
        self.docs_endpoint_name = docs_endpoint_name
        self.product_ids: list[str] = []

        # A dict is used to track the product routers so we can ensure
        # idempotentcy in case a product is added multiple times, and also to
        # manage clobbering if multiple products with the same product_id are
        # added.
        self.product_routers: dict[str, ProductRouter] = {}

        self.register_route(
            Route(
                name=ROOT,
                tag=Tag.ROOT,
                path="/",
                endpoint=self.get_root,
                errors={},
                summary="Get the API landing page",
            )
        )
        self.register_route(
            Route(
                name=CONFORMANCE,
                tag=Tag.CONFORMANCE,
                path="/conformance",
                endpoint=self.get_conformance,
                errors={},
                summary="Get conformance urls for the API",
            )
        )
        self.register_route(
            Route(
                name=LIST_PRODUCTS,
                tag=Tag.PRODUCTS,
                path="/products",
                endpoint=self.get_products,
                errors=NOT_FOUND,
                summary="List all Products",
            )
        )
        self.register_route(
            Route(
                name=LIST_ORDERS,
                tag=Tag.ORDERS,
                path="/orders",
                endpoint=self.get_orders,
                errors=NOT_FOUND | SERVER_ERROR,
                summary="List all Orders",
                response_class=GeoJSONResponse,
            )
        )
        self.register_route(
            Route(
                name=GET_ORDER,
                tag=Tag.ORDERS,
                path="/orders/{orderId}",
                endpoint=self.get_order,
                errors=NOT_FOUND | SERVER_ERROR,
                summary="Get an Order by ID",
                response_class=GeoJSONResponse,
            )
        )

        if self.supports_order_statuses:
            _conformances.add(API_CONFORMANCE.order_statuses)
            self.register_route(
                Route(
                    name=LIST_ORDER_STATUSES,
                    tag=Tag.ORDERS,
                    path="/orders/{orderId}/statuses",
                    endpoint=self.get_order_statuses,
                    errors=NOT_FOUND | SERVER_ERROR,
                    summary="List statuses for an Order",
                )
            )

        if self.supports_async_opportunity_search:
            _conformances.add(API_CONFORMANCE.searches_opportunity)
            self.register_route(
                Route(
                    name=LIST_OPPORTUNITY_SEARCH_RECORDS,
                    tag=Tag.OPPORTUNITIES,
                    path="/searches/opportunities",
                    endpoint=self.get_opportunity_search_records,
                    errors=NOT_FOUND | SERVER_ERROR,
                    summary="List all Opportunity Search Records",
                )
            )
            self.register_route(
                Route(
                    name=GET_OPPORTUNITY_SEARCH_RECORD,
                    tag=Tag.OPPORTUNITIES,
                    path="/searches/opportunities/{searchRecordId}",
                    endpoint=self.get_opportunity_search_record,
                    errors=NOT_FOUND | SERVER_ERROR,
                    summary="Get an Opportunity Search Record by ID",
                )
            )

            if self.__get_opportunity_search_record_statuses is not None:
                _conformances.add(API_CONFORMANCE.searches_opportunity_statuses)
                self.register_route(
                    Route(
                        name=LIST_OPPORTUNITY_SEARCH_RECORD_STATUSES,
                        tag=Tag.OPPORTUNITIES,
                        path="/searches/opportunities/{searchRecordId}/statuses",
                        endpoint=self.get_opportunity_search_record_statuses,
                        errors=NOT_FOUND | SERVER_ERROR,
                        summary="List statuses for an Opportunity Search Record",
                    )
                )

        self.conformances = sorted(_conformances)

    def get_root(self, request: Request) -> RootResponse:
        links = [
            json_link(
                "self",
                self.url_for(request, self.route_name(ROOT)),
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
            json_link("conformance", href=self.url_for(request, self.route_name(CONFORMANCE))),
            json_link("products", self.url_for(request, self.route_name(LIST_PRODUCTS))),
            Link(
                rel="orders",
                href=self.url_for(request, self.route_name(LIST_ORDERS)),
                type=TYPE_GEOJSON,
            ),
        ]

        if self.supports_async_opportunity_search:
            links.append(
                json_link(
                    "search-records",
                    self.url_for(request, self.route_name(LIST_OPPORTUNITY_SEARCH_RECORDS)),
                ),
            )

        return RootResponse(
            id="STAPI API",
            conforms_to=self.conformances,
            links=links,
        )

    def get_conformance(self) -> Conformance:
        return Conformance(conforms_to=self.conformances)

    def get_products(self, request: Request, next: NextToken = None, limit: Limit = DEFAULT_LIMIT) -> ProductCollection:
        start = 0
        if next:
            try:
                start = self.product_ids.index(next)
            except ValueError:
                raise NotFoundError(detail="Error finding pagination token for products") from None

        end = start + limit
        page = Page(
            items=[self.product_routers[product_id].get_product(request) for product_id in self.product_ids[start:end]],
            next_token=Some(self.product_ids[end]) if end < len(self.product_ids) else Nothing,
            number_matched=Some(len(self.product_ids)),
        )
        return ProductCollection(
            products=page.items,
            links=self.page_links(request, page, self.route_name(LIST_PRODUCTS), limit),
            number_matched=page.number_matched.value_or(None),
        )

    async def get_orders(
        self, request: Request, next: NextToken = None, limit: Limit = DEFAULT_LIMIT
    ) -> OrderCollection[OrderStatus]:
        match await self._get_orders(next, limit, request):
            case Success(page):
                for order in page.items:
                    order.links.extend(self.order_links(order, request))
                return OrderCollection(
                    features=page.items,
                    links=self.page_links(request, page, self.route_name(LIST_ORDERS), limit, media_type=TYPE_GEOJSON),
                    number_matched=page.number_matched.value_or(None),
                )
            case Failure(PaginationTokenError()):
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

    async def get_order(self, order_id: OrderIdPath, request: Request) -> Order[OrderStatus]:
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
        order_id: OrderIdPath,
        request: Request,
        next: NextToken = None,
        limit: Limit = DEFAULT_LIMIT,
    ) -> OrderStatusCollection:
        match await self._get_order_statuses(order_id, next, limit, request):
            case Success(Some(page)):
                return OrderStatusCollection(
                    statuses=page.items,
                    links=self.page_links(request, page, self.route_name(LIST_ORDER_STATUSES), limit, orderId=order_id),
                    number_matched=page.number_matched.value_or(None),
                )
            case Success(Maybe.empty):
                raise NotFoundError("Order not found")
            case Failure(PaginationTokenError()):
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

    def add_product(self, product: Product, *args: Any, **kwargs: Any) -> None:
        # Give the include a prefix from the product router
        product_router = ProductRouter(product, self, *args, **kwargs)
        self.include_router(product_router, prefix=f"/products/{product.id}")
        self.product_routers[product.id] = product_router
        self.product_ids = [*self.product_routers.keys()]

    def generate_order_href(self, request: Request, order_id: str) -> URL:
        return self.url_for(request, self.route_name(GET_ORDER), orderId=order_id)

    def generate_order_statuses_href(self, request: Request, order_id: str) -> URL:
        return self.url_for(request, self.route_name(LIST_ORDER_STATUSES), orderId=order_id)

    def order_links(self, order: Order[OrderStatus], request: Request) -> list[Link]:
        """Links added to every order response."""
        links = [
            Link(
                href=self.generate_order_href(request, order.id),
                rel="self",
                type=TYPE_GEOJSON,
            ),
        ]
        if self.supports_order_statuses:
            links.append(
                json_link(
                    "monitor",
                    self.generate_order_statuses_href(request, order.id),
                )
            )
        return links

    async def get_opportunity_search_records(
        self, request: Request, next: NextToken = None, limit: Limit = DEFAULT_LIMIT
    ) -> OpportunitySearchRecordCollection:
        match await self._get_opportunity_search_records(next, limit, request):
            case Success(page):
                for record in page.items:
                    record.links.extend(self.opportunity_search_record_links(record, request))
                return OpportunitySearchRecordCollection(
                    records=page.items,
                    links=self.page_links(request, page, self.route_name(LIST_OPPORTUNITY_SEARCH_RECORDS), limit),
                    number_matched=page.number_matched.value_or(None),
                )
            case Failure(PaginationTokenError()):
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

    async def get_opportunity_search_record(
        self, search_record_id: SearchRecordIdPath, request: Request
    ) -> OpportunitySearchRecord:
        """
        Get the Opportunity Search Record with `search_record_id`.
        """
        match await self._get_opportunity_search_record(search_record_id, request):
            case Success(Some(search_record)):
                search_record.links.extend(self.opportunity_search_record_links(search_record, request))
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
        self,
        search_record_id: SearchRecordIdPath,
        request: Request,
        next: NextToken = None,
        limit: Limit = DEFAULT_LIMIT,
    ) -> OpportunitySearchStatusCollection:
        """
        Get the Opportunity Search Record statuses with `searchRecordId`.
        """
        match await self._get_opportunity_search_record_statuses(search_record_id, next, limit, request):
            case Success(Some(page)):
                return OpportunitySearchStatusCollection(
                    statuses=page.items,
                    links=self.page_links(
                        request,
                        page,
                        self.route_name(LIST_OPPORTUNITY_SEARCH_RECORD_STATUSES),
                        limit,
                        searchRecordId=search_record_id,
                    ),
                    number_matched=page.number_matched.value_or(None),
                )
            case Success(Maybe.empty):
                raise NotFoundError("Opportunity Search Record not found")
            case Failure(PaginationTokenError()):
                raise NotFoundError("Error finding pagination token")
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
            self.route_name(GET_OPPORTUNITY_SEARCH_RECORD),
            searchRecordId=search_record_id,
        )

    def generate_opportunity_search_record_statuses_href(self, request: Request, search_record_id: str) -> URL:
        return self.url_for(
            request,
            self.route_name(LIST_OPPORTUNITY_SEARCH_RECORD_STATUSES),
            searchRecordId=search_record_id,
        )

    def opportunity_search_record_links(
        self, opportunity_search_record: OpportunitySearchRecord, request: Request
    ) -> list[Link]:
        """Links added to every search record response."""
        links = [self.opportunity_search_record_self_link(opportunity_search_record, request)]
        if self.supports_opportunity_search_record_statuses:
            links.append(
                json_link(
                    "monitor",
                    self.generate_opportunity_search_record_statuses_href(request, opportunity_search_record.id),
                )
            )
        return links

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
    def supports_opportunity_search_record_statuses(self) -> bool:
        """Whether the search-record-statuses endpoint is registered."""
        return self.supports_async_opportunity_search and self.__get_opportunity_search_record_statuses is not None

    @property
    def supports_order_statuses(self) -> bool:
        """Whether the order-statuses endpoint is registered."""
        return self.__get_order_statuses is not None

    @property
    def supports_async_opportunity_search(self) -> bool:
        return self.__get_opportunity_search_records is not None and self.__get_opportunity_search_record is not None
