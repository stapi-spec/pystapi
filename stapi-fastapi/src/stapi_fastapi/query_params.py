"""Query parameter annotations shared by the paginated collection endpoints."""

from typing import Annotated

from fastapi import Query
from pydantic import AfterValidator

MIN_LIMIT = 1
"""Smallest page size a client may request."""

MAX_LIMIT = 100
"""Largest page size the server will serve, however many a client asks for."""

DEFAULT_LIMIT = 10
"""Page size used when a client requests none."""


def clamp_limit(limit: int) -> int:
    """Hold a requested page size down to what the server will serve.

    The spec makes `limit` an upper bound the client *requests*, not one the
    server must honour, and publishes no maximum. An over-large ask is therefore
    answered with a smaller page rather than rejected, which is both what the
    client wanted and one round trip cheaper than making them ask again.
    """
    return min(limit, MAX_LIMIT)


#: Maximum number of items to return in a single page. Only the lower bound is
#: published, as in the spec; above `MAX_LIMIT` the page is quietly clamped.
Limit = Annotated[
    int,
    Query(
        ge=MIN_LIMIT,
        description="The maximum number of items to return in a single page.",
    ),
    AfterValidator(clamp_limit),
]

#: Opaque pagination token, as returned in the `next` link of a prior page.
NextToken = Annotated[
    str | None,
    Query(
        description="Pagination token, as provided by the `next` link of a previous response.",
    ),
]
