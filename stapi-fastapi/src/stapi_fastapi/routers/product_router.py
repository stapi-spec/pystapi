from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING, Any

from fastapi import (
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from returns.maybe import Maybe, Some
from returns.result import Failure, Success
from stapi_pydantic import (
    Conformance,
    Geometry,
    JsonSchema,
    Link,
    OpportunityCollection,
    OpportunityRequest,
    OpportunitySearchRecord,
    Order,
    OrderRequest,
    OrderStatus,
    Prefer,
)
from stapi_pydantic import (
    Product as ProductPydantic,
)

from stapi_fastapi.conformance import PRODUCT as PRODUCT_CONFORMACES
from stapi_fastapi.constants import TYPE_GEOJSON, TYPE_JSON
from stapi_fastapi.errors import NotFoundError, PaginationTokenError, QueryablesError
from stapi_fastapi.models.product import Product
from stapi_fastapi.path_params import OpportunityCollectionIdPath
from stapi_fastapi.query_params import DEFAULT_LIMIT, Limit, NextToken, clamp_limit
from stapi_fastapi.responses import GeoJSONResponse
from stapi_fastapi.routers.base import BAD_REQUEST, NOT_FOUND, SERVER_ERROR, Route, StapiFastapiBaseRouter
from stapi_fastapi.routers.route_names import (
    CONFORMANCE,
    CREATE_ORDER,
    GET_OPPORTUNITY_COLLECTION,
    GET_ORDER_PARAMETERS,
    GET_PRODUCT,
    GET_QUERYABLES,
    SEARCH_OPPORTUNITIES,
    Tag,
)
from stapi_fastapi.routers.utils import json_link

if TYPE_CHECKING:
    from stapi_fastapi.routers import RootRouter

logger = logging.getLogger(__name__)


def get_prefer(prefer: str | None = Header(None)) -> str | None:
    if prefer is None:
        return None

    if prefer not in Prefer._value2member_map_:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Prefer header value: {prefer}",
        )

    return Prefer(prefer)


def build_conformances(product: Product, root_router: RootRouter) -> list[str]:
    # FIXME we can make this check more robust
    if not any(conformance.startswith("https://geojson.org/schema/") for conformance in product.conforms_to):
        raise ValueError("product conformance does not contain at least one geojson conformance")

    # The opportunity conformance classes are derived from what this router
    # actually serves: an async-only product mounted on a root router without
    # async support gets no opportunity routes, so declaring them is not enough.
    conformances = set(product.conforms_to) - {
        PRODUCT_CONFORMACES.opportunities,
        PRODUCT_CONFORMACES.opportunities_async,
    }

    if product.supports_opportunity_search:
        conformances.add(PRODUCT_CONFORMACES.opportunities)

    if product.supports_async_opportunity_search and root_router.supports_async_opportunity_search:
        conformances.add(PRODUCT_CONFORMACES.opportunities_async)

    return sorted(conformances)


class ProductRouter(StapiFastapiBaseRouter):
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
        self.route_name_prefix = (root_router.name, product.id)
        self.conformances = build_conformances(product, root_router)

        self.register_route(
            Route(
                name=GET_PRODUCT,
                tag=Tag.PRODUCTS,
                path="",
                endpoint=self.get_product,
                errors={},
                summary="Retrieve this product",
            )
        )
        self.register_route(
            Route(
                name=CONFORMANCE,
                tag=Tag.CONFORMANCE,
                path="/conformance",
                endpoint=self.get_product_conformance,
                errors={},
                summary="Get conformance urls for the product",
            )
        )
        self.register_route(
            Route(
                name=GET_QUERYABLES,
                tag=Tag.PRODUCTS,
                path="/queryables",
                endpoint=self.get_product_queryables,
                errors={},
                summary="Get queryables for the product",
            )
        )
        self.register_route(
            Route(
                name=GET_ORDER_PARAMETERS,
                tag=Tag.PRODUCTS,
                path="/order-parameters",
                endpoint=self.get_product_order_parameters,
                errors={},
                summary="Get order parameters for the product",
            )
        )

        # This wraps `self.create_order` to explicitly parameterize `OrderRequest`
        # for this Product. This must be done programmatically instead of with a type
        # annotation because it's setting the type dynamically instead of statically, and
        # pydantic needs this type annotation when doing object conversion. This cannot be done
        # directly to `self.create_order` because doing it there changes
        # the annotation on every `ProductRouter` instance's `create_order`, not just
        # this one's.
        async def _create_order(
            payload: OrderRequest,  # type: ignore
            request: Request,
            response: Response,
        ) -> Order[OrderStatus]:
            return await self.create_order(payload, request, response)

        _create_order.__annotations__["payload"] = OrderRequest[
            self.product.order_parameters  # type: ignore
        ]

        self.register_route(
            Route(
                name=CREATE_ORDER,
                tag=Tag.ORDERS,
                path="/orders",
                endpoint=_create_order,
                methods=("POST",),
                errors=BAD_REQUEST | SERVER_ERROR,
                summary="Create an order for the product",
                response_class=GeoJSONResponse,
                status_code=status.HTTP_201_CREATED,
            )
        )

        if product.supports_opportunity_search or (
            self.product.supports_async_opportunity_search and self.root_router.supports_async_opportunity_search
        ):
            self.register_route(
                Route(
                    name=SEARCH_OPPORTUNITIES,
                    tag=Tag.OPPORTUNITIES,
                    path="/opportunities",
                    endpoint=self.search_opportunities,
                    methods=("POST",),
                    errors=BAD_REQUEST | NOT_FOUND | SERVER_ERROR,
                    summary="Search Opportunities for the product",
                    response_class=GeoJSONResponse,
                    # unknown why mypy can't see the queryables property on Product, ignoring
                    response_model=OpportunityCollection[
                        Geometry,
                        self.product.opportunity_properties,  # type: ignore
                    ],
                    responses={
                        201: {
                            "model": OpportunitySearchRecord,
                            "content": {TYPE_JSON: {}},
                        }
                    },
                )
            )

        if product.supports_async_opportunity_search and root_router.supports_async_opportunity_search:
            self.register_route(
                Route(
                    name=GET_OPPORTUNITY_COLLECTION,
                    tag=Tag.OPPORTUNITIES,
                    path="/opportunities/{opportunityCollectionId}",
                    endpoint=self.get_opportunity_collection,
                    errors=NOT_FOUND | SERVER_ERROR,
                    summary="Get an Opportunity Collection by ID",
                    response_class=GeoJSONResponse,
                )
            )

    def get_product(self, request: Request) -> ProductPydantic:
        links = [
            json_link("self", self.url_for(request, self.route_name(GET_PRODUCT))),
            json_link("conformance", self.url_for(request, self.route_name(CONFORMANCE))),
            json_link("queryables", self.url_for(request, self.route_name(GET_QUERYABLES))),
            json_link(
                "order-parameters",
                self.url_for(request, self.route_name(GET_ORDER_PARAMETERS)),
            ),
            Link(
                href=self.url_for(request, self.route_name(CREATE_ORDER)),
                rel="create-order",
                type=TYPE_JSON,
                method="POST",
            ),
        ]

        if self.product.supports_opportunity_search or (
            self.product.supports_async_opportunity_search and self.root_router.supports_async_opportunity_search
        ):
            links.append(
                json_link(
                    "opportunities",
                    self.url_for(request, self.route_name(SEARCH_OPPORTUNITIES)),
                ),
            )

        return self.product.with_links(links=links)

    async def search_opportunities(
        self,
        search: OpportunityRequest,
        request: Request,
        response: Response,
        prefer: Prefer | None = Depends(get_prefer),
    ) -> OpportunityCollection | Response:  # type: ignore
        """
        Explore the opportunities available for a particular set of queryables
        """
        # sync
        if not (
            self.root_router.supports_async_opportunity_search and self.product.supports_async_opportunity_search
        ) or (prefer is Prefer.wait and self.product.supports_opportunity_search):
            return await self.search_opportunities_sync(
                search,
                request,
                response,
                prefer,
            )

        # async
        if (
            prefer is None
            or prefer is Prefer.respond_async
            or (prefer is Prefer.wait and not self.product.supports_opportunity_search)
        ):
            return await self.search_opportunities_async(search, request, prefer)

        raise AssertionError("Expected code to be unreachable")

    async def search_opportunities_sync(
        self,
        search: OpportunityRequest,
        request: Request,
        response: Response,
        prefer: Prefer | None,
    ) -> OpportunityCollection:  # type: ignore
        # The POST body carries its own `limit`, so it is held to the same bound
        # as the GET collections' query parameter. Its lower bound is the
        # model's, so only the clamp is applied here.
        limit = DEFAULT_LIMIT if search.limit is None else clamp_limit(search.limit)

        self.product.validate_required_queryables(search.search_parameters)
        links: list[Link] = []
        match await self.product.search_opportunities(
            self,
            search,
            search.next,
            limit,
            request,
        ):
            case Success(page):
                links.extend(page.links)
                links.append(self.order_link(request, search))
                next_token = page.next_token.value_or(None)
                if next_token is not None:
                    links.append(self.search_pagination_link(request, search, next_token))
            case Failure(e) if isinstance(e, QueryablesError):
                raise e
            case Failure(PaginationTokenError()):
                raise NotFoundError(detail="Error finding pagination token")
            case Failure(e):
                logger.error(
                    "An error occurred while searching opportunities: %s",
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error searching opportunities",
                )
            case x:
                raise AssertionError(f"Expected code to be unreachable {x}")

        if prefer is Prefer.wait and self.root_router.supports_async_opportunity_search:
            response.headers["Preference-Applied"] = "wait"

        return OpportunityCollection(
            features=page.items,
            links=links,
            number_matched=page.number_matched.value_or(None),
        )

    async def search_opportunities_async(
        self,
        search: OpportunityRequest,
        request: Request,
        prefer: Prefer | None,
    ) -> JSONResponse:
        self.product.validate_required_queryables(search.search_parameters)
        match await self.product.search_opportunities_async(self, search, request):
            case Success(search_record):
                search_record.links.extend(self.root_router.opportunity_search_record_links(search_record, request))
                headers = {}
                headers["Location"] = str(
                    self.root_router.generate_opportunity_search_record_href(request, search_record.id)
                )
                if prefer is not None:
                    headers["Preference-Applied"] = "respond-async"
                return JSONResponse(
                    status_code=201,
                    content=search_record.model_dump(mode="json"),
                    headers=headers,
                )
            case Failure(e) if isinstance(e, QueryablesError):
                raise e
            case Failure(e):
                logger.error(
                    "An error occurred while initiating an asynchronous opportunity search: %s",
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error initiating an asynchronous opportunity search",
                )
            case x:
                raise AssertionError(f"Expected code to be unreachable: {x}")

    def get_product_conformance(self) -> Conformance:
        """
        Return conformance urls of a specific product
        """
        return Conformance(conforms_to=self.conformances)

    def get_product_queryables(self) -> JsonSchema:
        """
        Return supported queryables of a specific product
        """
        return JsonSchema.from_model(self.product.queryables)

    def get_product_order_parameters(self) -> JsonSchema:
        """
        Return supported order parameters of a specific product
        """
        return JsonSchema.from_model(self.product.order_parameters)

    async def create_order(self, payload: OrderRequest, request: Request, response: Response) -> Order:  # type: ignore
        """
        Create a new order.
        """
        self.product.validate_required_queryables(payload.search_parameters)
        match await self.product.create_order(
            self,
            payload,
            request,
        ):
            case Success(order):
                order.links.extend(self.root_router.order_links(order, request))
                location = str(self.root_router.generate_order_href(request, order.id))
                response.headers["Location"] = location
                return order  # type: ignore
            case Failure(e) if isinstance(e, QueryablesError):
                raise e
            case Failure(e):
                logger.error(
                    "An error occurred while creating order: %s",
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error creating order",
                )
            case x:
                raise AssertionError(f"Expected code to be unreachable {x}")

    def order_link(self, request: Request, opp_req: OpportunityRequest) -> Link:
        return Link(
            href=self.url_for(request, self.route_name(CREATE_ORDER)),
            rel="create-order",
            type=TYPE_JSON,
            method="POST",
            body=opp_req.search_body(),
        )

    def search_pagination_link(self, request: Request, opp_req: OpportunityRequest, pagination_token: str) -> Link:
        """A `next` link for an opportunity search, whose parameters are a POST body.

        Distinct from the base router's query-parameter one: paging a search
        means re-POSTing the search body with a new token, not following a URL.
        """
        body = opp_req.body()
        body["next"] = pagination_token
        return Link(
            href=request.url,
            rel="next",
            type=TYPE_GEOJSON,
            method="POST",
            body=body,
        )

    async def get_opportunity_collection(
        self,
        opportunity_collection_id: OpportunityCollectionIdPath,
        request: Request,
        next: NextToken = None,
        limit: Limit = DEFAULT_LIMIT,
    ) -> OpportunityCollection:  # type: ignore
        """
        Fetch an opportunity collection generated by an asynchronous opportunity search.
        """
        match await self.product.get_opportunity_collection(
            self,
            opportunity_collection_id,
            next,
            limit,
            request,
        ):
            case Success(Some(page)):
                return OpportunityCollection(
                    id=opportunity_collection_id,
                    features=page.items,
                    links=self.page_links(
                        request,
                        page,
                        self.route_name(GET_OPPORTUNITY_COLLECTION),
                        limit,
                        media_type=TYPE_GEOJSON,
                        opportunityCollectionId=opportunity_collection_id,
                    ),
                    number_matched=page.number_matched.value_or(None),
                )
            case Success(Maybe.empty):
                raise NotFoundError("Opportunity Collection not found")
            case Failure(PaginationTokenError()):
                raise NotFoundError("Error finding pagination token")
            case Failure(e):
                logger.error(
                    "An error occurred while fetching opportunity collection: '%s': %s",
                    opportunity_collection_id,
                    traceback.format_exception(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error fetching Opportunity Collection",
                )
            case x:
                raise AssertionError(f"Expected code to be unreachable {x}")
