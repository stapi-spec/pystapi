from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from fastapi import Request
from returns.maybe import Maybe
from returns.result import ResultE
from stapi_pydantic import (
    OpportunitySearchRecord,
    OpportunitySearchStatus,
    Order,
    OrderStatus,
)

from stapi_fastapi.pagination import Page

GetOrders = Callable[
    [str | None, int, Request],
    Coroutine[Any, Any, ResultE[Page[Order[OrderStatus]]]],
]
"""
Type alias for an async function that returns a page of existing Orders.

Args:
    next (str | None): A pagination token.
    limit (int): The maximum number of orders to return in a page.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[stapi_fastapi.pagination.Page[Order]].
      The page's `next_token` becomes the collection's `next` link and its
      `number_matched` becomes the collection's `numberMatched`.
    - Returning returns.result.Failure[stapi_fastapi.errors.PaginationTokenError]
      will result in a 404, which is how an unusable pagination token is reported.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""

GetOrder = Callable[[str, Request], Coroutine[Any, Any, ResultE[Maybe[Order[OrderStatus]]]]]
"""
Type alias for an async function that gets details for the order with `order_id`.

Args:
    order_id (str): The order ID.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[returns.maybe.Some[Order]] if order is found.
    - Should return returns.result.Success[returns.maybe.Nothing] if the order is not found or if access is denied.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""


T = TypeVar("T", bound=OrderStatus)


GetOrderStatuses = Callable[
    [str, str | None, int, Request],
    Coroutine[Any, Any, ResultE[Maybe[Page[T]]]],
]
"""
Type alias for an async function that gets a page of statuses for the order with
`order_id`.

Args:
    order_id (str): The order ID.
    next (str | None): A pagination token.
    limit (int): The maximum number of statuses to return in a page.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[returns.maybe.Some[stapi_fastapi.pagination.Page[OrderStatus]]]
      if the order is found.
    - Should return returns.result.Success[returns.maybe.Nothing] if the order is not found or if access is denied.
    - Returning returns.result.Failure[stapi_fastapi.errors.PaginationTokenError]
      will result in a 404, which is how an unusable pagination token is reported.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""

GetOpportunitySearchRecords = Callable[
    [str | None, int, Request],
    Coroutine[Any, Any, ResultE[Page[OpportunitySearchRecord]]],
]
"""
Type alias for an async function that gets a page of OpportunitySearchRecords for
all products.

Args:
    next (str | None): A pagination token.
    limit (int): The maximum number of search records to return in a page.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[stapi_fastapi.pagination.Page[OpportunitySearchRecord]].
    - Returning returns.result.Failure[stapi_fastapi.errors.PaginationTokenError]
      will result in a 404, which is how an unusable pagination token is reported.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""

GetOpportunitySearchRecord = Callable[[str, Request], Coroutine[Any, Any, ResultE[Maybe[OpportunitySearchRecord]]]]
"""
Type alias for an async function that gets the OpportunitySearchRecord with
`search_record_id`.

Args:
    search_record_id (str): The ID of the OpportunitySearchRecord.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[returns.maybe.Some[OpportunitySearchRecord]] if the search record is found.
    - Should return returns.result.Success[returns.maybe.Nothing] if the search record is not found or
      if access is denied.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""

GetOpportunitySearchRecordStatuses = Callable[
    [str, str | None, int, Request],
    Coroutine[Any, Any, ResultE[Maybe[Page[OpportunitySearchStatus]]]],
]
"""
Type alias for an async function that gets a page of statuses of the
OpportunitySearchRecord with `search_record_id`.

Args:
    search_record_id (str): The ID of the OpportunitySearchRecord.
    next (str | None): A pagination token.
    limit (int): The maximum number of statuses to return in a page.
    request (Request): FastAPI's Request object.

Returns:
    - Should return
      returns.result.Success[returns.maybe.Some[stapi_fastapi.pagination.Page[OpportunitySearchStatus]]]
      if the search record is found.
    - Should return returns.result.Success[returns.maybe.Nothing] if the search record is not found or
      if access is denied.
    - Returning returns.result.Failure[stapi_fastapi.errors.PaginationTokenError]
      will result in a 404, which is how an unusable pagination token is reported.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""
