"""The page contract shared by every list backend."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from returns.maybe import Maybe, Nothing
from stapi_pydantic import Link

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    """One page of a collection, as returned by a list backend."""

    items: list[T]
    """The items on this page, no more than the requested `limit` of them."""

    next_token: Maybe[str] = Nothing
    """Token identifying the page after this one, `Nothing` if this is the last."""

    number_matched: Maybe[int] = Nothing
    """Total items matching the request across all pages.

    `Nothing` means unknown, and `numberMatched` is omitted from the response.
    """

    links: list[Link] = field(default_factory=list)
    """Collection-level links only the backend can know, e.g. `create-order` on
    an Opportunity Collection. The handler adds `self` and `next` itself.
    """
