from collections.abc import AsyncIterator, Callable, Generator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from stapi_fastapi.conformance import API
from stapi_fastapi.models.product import (
    Product,
)
from stapi_fastapi.routers.root_router import RootRouter

from .backends import (
    AnyOpportunity,
    mock_get_opportunity_search_record,
    mock_get_opportunity_search_record_statuses,
    mock_get_opportunity_search_records,
    mock_get_order,
    mock_get_order_statuses,
    mock_get_orders,
)
from .shared import (
    AssertLink,
    InMemoryOpportunityDB,
    InMemoryOrderDB,
    create_mock_opportunity,
    find_link,
    product_test_satellite_provider_sync_opportunity,
    product_test_spotlight_sync_opportunity,
)
from .test_datetime_interval import rfc3339_strftime


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    yield "http://stapiserver"


@pytest.fixture
def mock_products(request: pytest.FixtureRequest) -> list[Product]:
    marker = request.node.get_closest_marker("mock_products")
    if marker is not None:
        marked_products: list[Product] = marker.args[0]
        return marked_products
    return [
        product_test_spotlight_sync_opportunity,
        product_test_satellite_provider_sync_opportunity,
    ]


@pytest.fixture
def mock_opportunities() -> list[AnyOpportunity]:
    return [create_mock_opportunity()]


@pytest.fixture
def root_router_kwargs(request: pytest.FixtureRequest) -> dict[str, Any]:
    """Per-test overrides for the RootRouter the client fixtures build.

    Mark a test with `@pytest.mark.root_router_kwargs({...})` to add or replace
    router arguments; pass None for a backend to withhold it, which is how a
    capability is turned off.
    """
    marker = request.node.get_closest_marker("root_router_kwargs")
    return dict(marker.args[0]) if marker is not None else {}


def _root_router(overrides: dict[str, Any], **defaults: Any) -> RootRouter:
    kwargs = {**defaults, **overrides}
    return RootRouter(**{k: v for k, v in kwargs.items() if v is not None})


@pytest.fixture
def stapi_client(
    mock_products: list[Product],
    base_url: str,
    mock_opportunities: list[AnyOpportunity],
    root_router_kwargs: dict[str, Any],
) -> Generator[TestClient, None, None]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {
                "_orders_db": InMemoryOrderDB(),
                "_opportunities": mock_opportunities,
            }
        finally:
            pass

    root_router = _root_router(
        root_router_kwargs,
        get_orders=mock_get_orders,
        get_order=mock_get_order,
        get_order_statuses=mock_get_order_statuses,
        conformances=[API.core],
    )

    for mock_product in mock_products:
        root_router.add_product(mock_product)

    app = FastAPI(lifespan=lifespan)
    app.include_router(root_router, prefix="")

    with TestClient(app, base_url=f"{base_url}") as client:
        yield client


@pytest.fixture
def stapi_client_async_opportunity(
    mock_products: list[Product],
    base_url: str,
    mock_opportunities: list[AnyOpportunity],
    root_router_kwargs: dict[str, Any],
) -> Generator[TestClient, None, None]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {
                "_orders_db": InMemoryOrderDB(),
                "_opportunities_db": InMemoryOpportunityDB(),
                "_opportunities": mock_opportunities,
            }
        finally:
            pass

    root_router = _root_router(
        root_router_kwargs,
        get_orders=mock_get_orders,
        get_order=mock_get_order,
        get_order_statuses=mock_get_order_statuses,
        get_opportunity_search_records=mock_get_opportunity_search_records,
        get_opportunity_search_record=mock_get_opportunity_search_record,
        get_opportunity_search_record_statuses=mock_get_opportunity_search_record_statuses,
        conformances=[
            API.core,
            API.searches_opportunity,
            API.searches_opportunity_statuses,
        ],
    )

    for mock_product in mock_products:
        root_router.add_product(mock_product)

    app = FastAPI(lifespan=lifespan)
    app.include_router(root_router, prefix="")

    with TestClient(app, base_url=f"{base_url}") as client:
        yield client


@pytest.fixture(scope="session")
def url_for(base_url: str) -> Iterator[Callable[[str], str]]:
    def with_trailing_slash(value: str) -> str:
        return value if value.endswith("/") else f"{value}/"

    def url_for(value: str) -> str:
        return urljoin(with_trailing_slash(base_url), f"./{value.lstrip('/')}")

    yield url_for


@pytest.fixture
def assert_link(url_for: Callable[[str], str]) -> AssertLink:
    def _assert_link(
        req: str,
        body: dict[str, Any],
        rel: str,
        path: str,
        media_type: str = "application/json",
        method: str | None = None,
    ) -> None:
        link = find_link(body["links"], rel)
        assert link, f"{req} Link[rel={rel}] should exist"
        assert link["type"] == media_type
        assert link["href"] == url_for(path)
        if method:
            assert link["method"] == method

    return _assert_link


@pytest.fixture
def limit() -> int:
    return 10


@pytest.fixture
def opportunity_search(limit: int) -> dict[str, Any]:
    now = datetime.now(UTC)
    end = now + timedelta(days=5)
    format = "%Y-%m-%dT%H:%M:%S.%f%z"
    start_string = rfc3339_strftime(now, format)
    end_string = rfc3339_strftime(end, format)

    return {
        "search_parameters": {
            "geometry": {
                "type": "Point",
                "coordinates": [0, 0],
            },
            "datetime": f"{start_string}/{end_string}",
            "filter": {
                "op": "and",
                "args": [
                    {"op": ">", "args": [{"property": "off_nadir"}, 0]},
                    {"op": "<", "args": [{"property": "off_nadir"}, 45]},
                ],
            },
        },
        "limit": limit,
    }
