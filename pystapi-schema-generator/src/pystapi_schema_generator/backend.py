from fastapi import Request
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, ResultE, Success
from stapi_pydantic import Order, OrderStatus


async def stapi_get_orders(
    next: str | None, limit: int, request: Request
) -> ResultE[tuple[list[Order[OrderStatus]], Maybe[str]]]:
    """
    Return orders from backend.  Handle pagination/limit if applicable
    """
    try:
        start = 0
        limit = min(limit, 100)
        order_ids = [*request.state._orders_db._orders.keys()]

        if next:
            start = order_ids.index(next)
        end = start + limit
        ids = order_ids[start:end]
        orders = [request.state._orders_db.get_order(order_id) for order_id in ids]

        if end > 0 and end < len(order_ids):
            return Success((orders, Some(request.state._orders_db._orders[order_ids[end]].id)))
        return Success((orders, Nothing))
    except Exception as e:
        return Failure(e)


async def stapi_get_order(order_id: str, request: Request) -> ResultE[Maybe[Order[OrderStatus]]]:
    """
    Show details for order with `order_id`.
    """
    try:
        return Success(Maybe.from_optional(request.state._orders_db.get_order(order_id)))
    except Exception as e:
        return Failure(e)


async def stapi_get_order_statuses(
    order_id: str, next: str | None, limit: int, request: Request
) -> ResultE[Maybe[tuple[list[OrderStatus], Maybe[str]]]]:
    try:
        start = 0
        limit = min(limit, 100)
        statuses = request.state._orders_db.get_order_statuses(order_id)
        if statuses is None:
            return Success(Nothing)

        if next:
            start = int(next)
        end = start + limit
        stati = statuses[start:end]

        if end > 0 and end < len(statuses):
            return Success(Some((stati, Some(str(end)))))
        return Success(Some((stati, Nothing)))
    except Exception as e:
        return Failure(e)
