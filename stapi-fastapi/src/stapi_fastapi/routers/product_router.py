from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING, Any

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from geojson_pydantic.geometries import Geometry
from returns.maybe import Maybe, Some
from returns.result import Failure, Success
from stapi_pydantic import (
    Conformance,
    JsonSchemaModel,
    Link,
    OpportunityCollection,
    OpportunityPayload,
    OpportunitySearchRecord,
    Order,
    OrderPayload,
    OrderStatus,
    Prefer,
)
from stapi_pydantic import (
    Product as ProductPydantic,
)

from stapi_fastapi.conformance import PRODUCT as PRODUCT_CONFORMACES
from stapi_fastapi.constants import TYPE_JSON
from stapi_fastapi.errors import NotFoundError, QueryablesError
from stapi_fastapi.models.product import Product
from stapi_fastapi.responses import GeoJSONResponse
from stapi_fastapi.routers.route_names import (
    CONFORMANCE,
    CREATE_ORDER,
    GET_OPPORTUNITY_COLLECTION,
    GET_ORDER_PARAMETERS,
    GET_PRODUCT,
    GET_QUERYABLES,
    SEARCH_OPPORTUNITIES,
)

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
    if not any(conformance.startswith("https://geojson.org/schema/") for conformance in product.conformsTo):
        raise ValueError("product conformance does not contain at least one geojson conformance")

    conformances = set(product.conformsTo)

    if product.supports_opportunity_search:
        conformances.add(PRODUCT_CONFORMACES.opportunities)

    if product.supports_async_opportunity_search and root_router.supports_async_opportunity_search:
        conformances.add(PRODUCT_CONFORMACES.opportunities)
        conformances.add(PRODUCT_CONFORMACES.opportunities_async)

    return list(conformances)


class ProductRouter(APIRouter):
    # FIXME ruff is complaining that the init is too complex
    def __init__(  # noqa
        self,
        product: Product,
        root_router: RootRouter,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.product = product
        self.root_router = root_router
        self.conformances = build_conformances(product, root_router)

        self.add_api_route(
            path="",
            endpoint=self.get_product,
            name=f"{self.root_router.name}:{self.product.id}:{GET_PRODUCT}",
            methods=["GET"],
            summary="Retrieve this product",
            tags=["Products"],
        )

        self.add_api_route(
            path="/conformance",
            endpoint=self.get_product_conformance,
            name=f"{self.root_router.name}:{self.product.id}:{CONFORMANCE}",
            methods=["GET"],
            summary="Get conformance urls for the product",
            tags=["Products"],
        )

        self.add_api_route(
            path="/queryables",
            endpoint=self.get_product_queryables,
            name=f"{self.root_router.name}:{self.product.id}:{GET_QUERYABLES}",
            methods=["GET"],
            summary="Get queryables for the product",
            tags=["Products"],
        )

        self.add_api_route(
            path="/order-parameters",
            endpoint=self.get_product_order_parameters,
            name=f"{self.root_router.name}:{self.product.id}:{GET_ORDER_PARAMETERS}",
            methods=["GET"],
            summary="Get order parameters for the product",
            tags=["Products"],
        )

        # This wraps `self.create_order` to explicitly parameterize `OrderRequest`
        # for this Product. This must be done programmatically instead of with a type
        # annotation because it's setting the type dynamically instead of statically, and
        # pydantic needs this type annotation when doing object conversion. This cannot be done
        # directly to `self.create_order` because doing it there changes
        # the annotation on every `ProductRouter` instance's `create_order`, not just
        # this one's.
        async def _create_order(
            payload: OrderPayload,  # type: ignore
            request: Request,
            response: Response,
        ) -> Order[OrderStatus]:
            return await self.create_order(payload, request, response)

        _create_order.__annotations__["payload"] = OrderPayload[
            self.product.order_parameters  # type: ignore
        ]

        self.add_api_route(
            path="/orders",
            endpoint=_create_order,
            name=f"{self.root_router.name}:{self.product.id}:{CREATE_ORDER}",
            methods=["POST"],
            response_class=GeoJSONResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create an order for the product",
            tags=["Products"],
        )

        if product.supports_opportunity_search or (
            self.product.supports_async_opportunity_search and self.root_router.supports_async_opportunity_search
        ):
            self.add_api_route(
                path="/opportunities",
                endpoint=self.search_opportunities,
                name=f"{self.root_router.name}:{self.product.id}:{SEARCH_OPPORTUNITIES}",
                methods=["POST"],
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
                summary="Search Opportunities for the product",
                tags=["Products"],
            )

        if product.supports_async_opportunity_search and root_router.supports_async_opportunity_search:
            self.add_api_route(
                path="/opportunities/{opportunity_collection_id}",
                endpoint=self.get_opportunity_collection,
                name=f"{self.root_router.name}:{self.product.id}:{GET_OPPORTUNITY_COLLECTION}",
                methods=["GET"],
                response_class=GeoJSONResponse,
                summary="Get an Opportunity Collection by ID",
                tags=["Products"],
            )

    def get_product(self, request: Request) -> ProductPydantic:
        links = [
            Link(
                href=str(
                    request.url_for(
                        f"{self.root_router.name}:{self.product.id}:{GET_PRODUCT}",
                    ),
                ),
                rel="self",
                type=TYPE_JSON,
            ),
            Link(
                href=str(
                    request.url_for(
                        f"{self.root_router.name}:{self.product.id}:{CONFORMANCE}",
                    ),
                ),
                rel="conformance",
                type=TYPE_JSON,
            ),
            Link(
                href=str(
                    request.url_for(
                        f"{self.root_router.name}:{self.product.id}:{GET_QUERYABLES}",
                    ),
                ),
                rel="queryables",
                type=TYPE_JSON,
            ),
            Link(
                href=str(
                    request.url_for(
                        f"{self.root_router.name}:{self.product.id}:{GET_ORDER_PARAMETERS}",
                    ),
                ),
                rel="order-parameters",
                type=TYPE_JSON,
            ),
            Link(
                href=str(
                    request.url_for(
                        f"{self.root_router.name}:{self.product.id}:{CREATE_ORDER}",
                    ),
                ),
                rel="create-order",
                type=TYPE_JSON,
                method="POST",
            ),
        ]

        if self.product.supports_opportunity_search or (
            self.product.supports_async_opportunity_search and self.root_router.supports_async_opportunity_search
        ):
            links.append(
                Link(
                    href=str(
                        request.url_for(
                            f"{self.root_router.name}:{self.product.id}:{SEARCH_OPPORTUNITIES}",
                        ),
                    ),
                    rel="opportunities",
                    type=TYPE_JSON,
                ),
            )

        return self.product.with_links(links=links)

    async def search_opportunities(
        self,
        search: OpportunityPayload,
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
        search: OpportunityPayload,
        request: Request,
        response: Response,
        prefer: Prefer | None,
    ) -> OpportunityCollection:  # type: ignore
        links: list[Link] = []
        match await self.product.search_opportunities(
            self,
            search,
            search.next,
            search.limit,
            request,
        ):
            case Success((features, maybe_pagination_token)):
                links.append(self.order_link(request, search))
                match maybe_pagination_token:
                    case Some(x):
                        links.append(self.pagination_link(request, search, x))
                    case Maybe.empty:
                        pass
            case Failure(e) if isinstance(e, QueryablesError):
                raise e
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

        return OpportunityCollection(features=features, links=links)

    async def search_opportunities_async(
        self,
        search: OpportunityPayload,
        request: Request,
        prefer: Prefer | None,
    ) -> JSONResponse:
        match await self.product.search_opportunities_async(self, search, request):
            case Success(search_record):
                search_record.links.append(self.root_router.opportunity_search_record_self_link(search_record, request))
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
        return Conformance.model_validate({"conforms_to": self.conformances})

    def get_product_queryables(self) -> JsonSchemaModel:
        """
        Return supported queryables of a specific product
        """
        return self.product.queryables

    def get_product_order_parameters(self) -> JsonSchemaModel:
        """
        Return supported order parameters of a specific product
        """
        return self.product.order_parameters

    async def create_order(self, payload: OrderPayload, request: Request, response: Response) -> Order:  # type: ignore
        """
        Create a new order.
        """
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

    def order_link(self, request: Request, opp_req: OpportunityPayload) -> Link:
        return Link(
            href=str(
                request.url_for(
                    f"{self.root_router.name}:{self.product.id}:{CREATE_ORDER}",
                ),
            ),
            rel="create-order",
            type=TYPE_JSON,
            method="POST",
            body=opp_req.search_body(),
        )

    def pagination_link(self, request: Request, opp_req: OpportunityPayload, pagination_token: str) -> Link:
        body = opp_req.body()
        body["next"] = pagination_token
        return Link(
            href=str(request.url),
            rel="next",
            type=TYPE_JSON,
            method="POST",
            body=body,
        )

    async def get_opportunity_collection(
        self, opportunity_collection_id: str, request: Request
    ) -> OpportunityCollection:  # type: ignore
        """
        Fetch an opportunity collection generated by an asynchronous opportunity search.
        """
        match await self.product.get_opportunity_collection(
            self,
            opportunity_collection_id,
            request,
        ):
            case Success(Some(opportunity_collection)):
                opportunity_collection.links.append(
                    Link(
                        href=str(
                            request.url_for(
                                f"{self.root_router.name}:{self.product.id}:{GET_OPPORTUNITY_COLLECTION}",
                                opportunity_collection_id=opportunity_collection_id,
                            ),
                        ),
                        rel="self",
                        type=TYPE_JSON,
                    ),
                )
                return opportunity_collection  # type: ignore
            case Success(Maybe.empty):
                raise NotFoundError("Opportunity Collection not found")
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
