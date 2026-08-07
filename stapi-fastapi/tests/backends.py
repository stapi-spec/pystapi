from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, ResultE, Success
from stapi_fastapi import Page
from stapi_fastapi.errors import PaginationTokenError
from stapi_fastapi.routers.product_router import ProductRouter
from stapi_pydantic import (
    Opportunity,
    OpportunityCollection,
    OpportunityRequest,
    OpportunitySearchRecord,
    OpportunitySearchStatus,
    OpportunitySearchStatusCode,
    Order,
    OrderProperties,
    OrderRequest,
    OrderStatus,
    OrderStatusCode,
    StoredOrderRequest,
)


def _offset(token: str) -> int:
    """Read a page offset out of a pagination token.

    The mocks encode the offset in the token itself, so anything unparseable is
    a token that identifies no page rather than an incidental error.
    """
    try:
        return int(token)
    except ValueError:
        raise PaginationTokenError(f"unusable pagination token: {token!r}") from None


async def mock_get_orders(
    next: str | None,
    limit: int,
    request: Request,
) -> ResultE[Page[Order]]:
    """
    Return orders from backend.  Handle pagination/limit if applicable
    """
    # Deliberately not len(order_ids): the tests assert that whatever the
    # backend reports as the total is what reaches `numberMatched`.
    count = 314
    try:
        start = 0
        limit = min(limit, 100)
        order_ids = [*request.state._orders_db._orders.keys()]

        if next:
            try:
                start = order_ids.index(next)
            except ValueError:
                raise PaginationTokenError(f"unknown pagination token: {next!r}") from None
        end = start + limit
        ids = order_ids[start:end]
        orders = [request.state._orders_db.get_order(order_id) for order_id in ids]

        next_token = Some(request.state._orders_db._orders[order_ids[end]].id) if end < len(order_ids) else Nothing
        return Success(Page(items=orders, next_token=next_token, number_matched=Some(count)))
    except Exception as e:
        return Failure(e)


async def mock_get_order(order_id: str, request: Request) -> ResultE[Maybe[Order]]:
    """
    Show details for order with `order_id`.
    """
    try:
        return Success(Maybe.from_optional(request.state._orders_db.get_order(order_id)))
    except Exception as e:
        return Failure(e)


async def mock_get_order_statuses(
    order_id: str, next: str | None, limit: int, request: Request
) -> ResultE[Maybe[Page[OrderStatus]]]:
    try:
        start = 0
        limit = min(limit, 100)
        statuses = request.state._orders_db.get_order_statuses(order_id)
        if statuses is None:
            return Success(Nothing)

        if next:
            start = _offset(next)
        end = start + limit

        return Success(
            Some(
                Page(
                    items=statuses[start:end],
                    next_token=Some(str(end)) if end < len(statuses) else Nothing,
                    number_matched=Some(len(statuses)),
                )
            )
        )
    except Exception as e:
        return Failure(e)


async def mock_create_order(product_router: ProductRouter, payload: OrderRequest, request: Request) -> ResultE[Order]:
    """
    Create a new order.
    """
    try:
        status = OrderStatus(
            timestamp=datetime.now(UTC),
            status_code=OrderStatusCode.received,
        )
        order = Order(
            id=str(uuid4()),
            geometry=payload.search_parameters.geometry,
            properties=OrderProperties(
                product_id=product_router.product.id,
                created=datetime.now(UTC),
                status=status,
                order_request=StoredOrderRequest(
                    search_parameters=payload.search_parameters,
                    # declared as BaseOrderParameters; pydantic validates the
                    # dumped dict into one at runtime
                    order_parameters=payload.order_parameters.model_dump(),  # type: ignore[arg-type]
                ),
            ),
            links=[],
        )

        request.state._orders_db.put_order(order)
        request.state._orders_db.put_order_status(order.id, status)
        return Success(order)
    except Exception as e:
        return Failure(e)


async def mock_search_opportunities(
    product_router: ProductRouter,
    search: OpportunityRequest,
    next: str | None,
    limit: int,
    request: Request,
) -> ResultE[Page[Opportunity]]:
    try:
        start = 0
        limit = min(limit, 100)
        if next:
            start = _offset(next)
        end = start + limit
        # Reflect the searched geometry into the returned opportunities.
        opportunities = [
            o.model_copy(update={"geometry": search.search_parameters.geometry})
            for o in request.state._opportunities[start:end]
        ]
        total = len(request.state._opportunities)
        # `end > 0` because the search body may ask for a limit of 0, and a
        # token pointing back at offset 0 would page forever.
        return Success(
            Page(
                items=opportunities,
                next_token=Some(str(end)) if 0 < end < total else Nothing,
                number_matched=Some(total),
            )
        )
    except Exception as e:
        return Failure(e)


async def mock_search_opportunities_async(
    product_router: ProductRouter,
    search: OpportunityRequest,
    request: Request,
) -> ResultE[OpportunitySearchRecord]:
    try:
        received_status = OpportunitySearchStatus(
            timestamp=datetime.now(UTC),
            status_code=OpportunitySearchStatusCode.received,
        )
        search_record = OpportunitySearchRecord(
            id=str(uuid4()),
            product_id=product_router.product.id,
            search_parameters=search.search_parameters,
            status=received_status,
            links=[],
        )
        request.state._opportunities_db.put_search_record(search_record)
        return Success(search_record)
    except Exception as e:
        return Failure(e)


async def mock_get_opportunity_collection(
    product_router: ProductRouter, opportunity_collection_id: str, request: Request
) -> ResultE[Maybe[OpportunityCollection]]:
    try:
        return Success(
            Maybe.from_optional(request.state._opportunities_db.get_opportunity_collection(opportunity_collection_id))
        )
    except Exception as e:
        return Failure(e)


async def mock_get_opportunity_search_records(
    next: str | None,
    limit: int,
    request: Request,
) -> ResultE[Page[OpportunitySearchRecord]]:
    try:
        start = 0
        limit = min(limit, 100)
        search_records = request.state._opportunities_db.get_search_records()

        if next:
            start = _offset(next)
        end = start + limit

        return Success(
            Page(
                items=search_records[start:end],
                next_token=Some(str(end)) if end < len(search_records) else Nothing,
                number_matched=Some(len(search_records)),
            )
        )
    except Exception as e:
        return Failure(e)


async def mock_get_opportunity_search_record(
    search_record_id: str, request: Request
) -> ResultE[Maybe[OpportunitySearchRecord]]:
    try:
        return Success(Maybe.from_optional(request.state._opportunities_db.get_search_record(search_record_id)))
    except Exception as e:
        return Failure(e)


async def mock_get_opportunity_search_record_statuses(
    search_record_id: str,
    next: str | None,
    limit: int,
    request: Request,
) -> ResultE[Maybe[Page[OpportunitySearchStatus]]]:
    try:
        statuses = request.state._opportunities_db.get_search_record_statuses(search_record_id)
        if statuses is None:
            return Success(Nothing)

        start = _offset(next) if next else 0
        end = start + limit
        return Success(
            Some(
                Page(
                    items=statuses[start:end],
                    next_token=Some(str(end)) if end < len(statuses) else Nothing,
                    number_matched=Some(len(statuses)),
                )
            )
        )
    except Exception as e:
        return Failure(e)
