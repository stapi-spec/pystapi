from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request
from returns.maybe import Maybe
from returns.result import ResultE
from stapi_pydantic.opportunity import (
    Opportunity,
    OpportunityCollection,
    OpportunityPayload,
    OpportunitySearchRecord,
)
from stapi_pydantic.order import Order, OrderPayload

from stapi_fastapi.routers.product_router import ProductRouter

SearchOpportunities = Callable[
    [ProductRouter, OpportunityPayload, str | None, int, Request],
    Coroutine[Any, Any, ResultE[tuple[list[Opportunity], Maybe[str]]]],  # type: ignore
]
"""
Type alias for an async function that searches for ordering opportunities for the given
search parameters.

Args:
    product_router (ProductRouter): The product router.
    search (OpportunityPayload): The search parameters.
    next (str | None): A pagination token.
    limit (int): The maximum number of opportunities to return in a page.
    request (Request): FastAPI's Request object.

Returns:
    A tuple containing a list of opportunities and a pagination token.

    - Should return returns.result.Success[tuple[list[Opportunity], returns.maybe.Some[str]]]
      if including a pagination token
    - Should return returns.result.Success[tuple[list[Opportunity], returns.maybe.Nothing]]
      if not including a pagination token
    - Returning returns.result.Failure[Exception] will result in a 500.

Note:
    Backends must validate search constraints and return
    returns.result.Failure[stapi_fastapi.errors.ConstraintsError] if not valid.
"""

SearchOpportunitiesAsync = Callable[
    [ProductRouter, OpportunityPayload, Request],
    Coroutine[Any, Any, ResultE[OpportunitySearchRecord]],
]
"""
Type alias for an async function that starts an asynchronous search for ordering
opportunities for the given search parameters.

Args:
    product_router (ProductRouter): The product router.
    search (OpportunityPayload): The search parameters.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[OpportunitySearchRecord]
    - Returning returns.result.Failure[Exception] will result in a 500.

Backends must validate search constraints and return
returns.result.Failure[stapi_fastapi.errors.ConstraintsError] if not valid.
"""

GetOpportunityCollection = Callable[
    [ProductRouter, str, Request],
    Coroutine[Any, Any, ResultE[Maybe[OpportunityCollection]]],  # type: ignore
]
"""
Type alias for an async function that retrieves the opportunity collection with
`opportunity_collection_id`.

The opportunity collection is generated by an asynchronous opportunity search.

Args:
    product_router (ProductRouter): The product router.
    opportunity_collection_id (str): The ID of the opportunity collection.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[returns.maybe.Some[OpportunityCollection]]
      if the opportunity collection is found.
    - Should return returns.result.Success[returns.maybe.Nothing] if the opportunity collection is not found or
      if access is denied.
    - Returning returns.result.Failure[Exception] will result in a 500.
"""

CreateOrder = Callable[[ProductRouter, OrderPayload, Request], Coroutine[Any, Any, ResultE[Order]]]  # type: ignore
"""
Type alias for an async function that creates a new order.

Args:
    product_router (ProductRouter): The product router.
    payload (OrderPayload): The order payload.
    request (Request): FastAPI's Request object.

Returns:
    - Should return returns.result.Success[Order]
    - Returning returns.result.Failure[Exception] will result in a 500.

Note:
    Backends must validate order payload and return
    returns.result.Failure[stapi_fastapi.errors.ConstraintsError] if not valid.
"""
