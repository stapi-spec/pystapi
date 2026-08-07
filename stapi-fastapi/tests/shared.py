from collections import defaultdict
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol, Self, TypeAlias
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from geojson_pydantic import Point
from geojson_pydantic.types import Position2D
from httpx import Response
from pydantic import BaseModel, Field, model_validator
from pytest import fail
from stapi_fastapi.conformance import PRODUCT
from stapi_fastapi.models.product import Product
from stapi_pydantic import (
    Opportunity,
    OpportunityProperties,
    OpportunitySearchRecord,
    OpportunitySearchStatus,
    Order,
    OrderParameters,
    OrderStatus,
    Provider,
    ProviderRole,
    Queryables,
)

from .backends import (
    AnyOpportunity,
    AnyOpportunityCollection,
    mock_create_order,
    mock_get_opportunity_collection,
    mock_search_opportunities,
    mock_search_opportunities_async,
)

link_dict: TypeAlias = dict[str, Any]


def find_link(links: list[link_dict], rel: str) -> link_dict | None:
    return next((link for link in links if link["rel"] == rel), None)


class AssertLink(Protocol):
    """Call signature of the `assert_link` fixture."""

    def __call__(
        self,
        req: str,
        body: dict[str, Any],
        rel: str,
        path: str,
        media_type: str = "application/json",
        method: str | None = None,
    ) -> None: ...


class InMemoryOrderDB:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._statuses: dict[str, list[OrderStatus]] = defaultdict(list)

    def get_order(self, order_id: str) -> Order | None:
        return deepcopy(self._orders.get(order_id))

    def get_orders(self) -> list[Order]:
        return deepcopy(list(self._orders.values()))

    def put_order(self, order: Order) -> None:
        self._orders[order.id] = deepcopy(order)

    def get_order_statuses(self, order_id: str) -> list[OrderStatus] | None:
        return deepcopy(self._statuses.get(order_id))

    def put_order_status(self, order_id: str, status: OrderStatus) -> None:
        self._statuses[order_id].append(deepcopy(status))


class InMemoryOpportunityDB:
    def __init__(self) -> None:
        self._search_records: dict[str, OpportunitySearchRecord] = {}
        self._statuses: dict[str, list[OpportunitySearchStatus]] = defaultdict(list)
        self._collections: dict[str, AnyOpportunityCollection] = {}

    def get_search_record(self, search_id: str) -> OpportunitySearchRecord | None:
        return deepcopy(self._search_records.get(search_id))

    def get_search_record_statuses(self, search_id: str) -> list[OpportunitySearchStatus] | None:
        if search_id not in self._search_records:
            return None
        return deepcopy(self._statuses[search_id])

    def get_search_records(self) -> list[OpportunitySearchRecord]:
        return deepcopy(list(self._search_records.values()))

    def put_search_record(self, search_record: OpportunitySearchRecord) -> None:
        """Store a search record, accumulating its status history."""
        self._search_records[search_record.id] = deepcopy(search_record)
        self._statuses[search_record.id].append(deepcopy(search_record.status))

    def get_opportunity_collection(self, collection_id: str) -> AnyOpportunityCollection | None:
        return deepcopy(self._collections.get(collection_id))

    def put_opportunity_collection(self, collection: AnyOpportunityCollection) -> None:
        if collection.id is None:
            raise ValueError("collection must have an id")
        self._collections[collection.id] = deepcopy(collection)


class MyProductQueryables(Queryables):
    off_nadir: int


class OffNadirRange(BaseModel):
    minimum: int = Field(ge=0, le=45)
    maximum: int = Field(ge=0, le=45)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.minimum > self.maximum:
            raise ValueError("range minimum cannot be greater than maximum")
        return self


class MyOpportunityProperties(OpportunityProperties):
    off_nadir: OffNadirRange
    vehicle_id: list[Literal[1, 2, 5, 7, 8]]
    platform: Literal["platform_id"]


class MyOrderParameters(OrderParameters):
    s3_path: str | None = None


provider = Provider(
    name="Test Provider",
    description="A provider for Test data",
    roles=[ProviderRole.producer],  # Example role
    url="https://test-provider.example.com",  # Must be a valid URL
)

product_test_spotlight = Product(
    id="test-spotlight",
    title="Test Spotlight Product",
    description="Test product for test spotlight",
    license="CC-BY-4.0",
    keywords=["test", "satellite"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=None,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.geojson_point],
)

product_test_spotlight_sync_opportunity = Product(
    id="test-spotlight",
    title="Test Spotlight Product",
    description="Test product for test spotlight",
    license="CC-BY-4.0",
    keywords=["test", "satellite"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=mock_search_opportunities,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.geojson_point],
)


product_test_spotlight_async_opportunity = Product(
    id="test-spotlight",
    title="Test Spotlight Product",
    description="Test product for test spotlight",
    license="CC-BY-4.0",
    keywords=["test", "satellite"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=None,
    search_opportunities_async=mock_search_opportunities_async,
    get_opportunity_collection=mock_get_opportunity_collection,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.geojson_point],
)

# Declares the opportunity conformance classes itself, the way a provider
# publishing an async-search product would. What is actually advertised depends
# on which routes the router ends up registering, not on this declaration.
product_test_spotlight_async_opportunity_declared_conformances = Product(
    id="test-spotlight",
    title="Test Spotlight Product",
    description="Test product for test spotlight",
    license="CC-BY-4.0",
    keywords=["test", "satellite"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=None,
    search_opportunities_async=mock_search_opportunities_async,
    get_opportunity_collection=mock_get_opportunity_collection,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.geojson_point, PRODUCT.opportunities, PRODUCT.opportunities_async],
)

product_test_spotlight_sync_async_opportunity = Product(
    id="test-spotlight",
    title="Test Spotlight Product",
    description="Test product for test spotlight",
    license="CC-BY-4.0",
    keywords=["test", "satellite"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=mock_search_opportunities,
    search_opportunities_async=mock_search_opportunities_async,
    get_opportunity_collection=mock_get_opportunity_collection,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.geojson_point],
)

product_test_satellite_provider_sync_opportunity = Product(
    id="test-satellite-provider",
    title="Satellite Product",
    description="A product by a satellite provider",
    license="CC-BY-4.0",
    keywords=["test", "satellite", "provider"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=mock_search_opportunities,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.geojson_point],
)


# Declares no geojson conformance, which a Product must do to say what geometry
# it accepts. Registering it is an error.
product_test_spotlight_no_geojson_conformance = Product(
    id="test-spotlight-no-geojson",
    title="Test Spotlight Product",
    description="Test product declaring no geojson conformance",
    license="CC-BY-4.0",
    keywords=["test", "satellite"],
    providers=[provider],
    links=[],
    create_order=mock_create_order,
    search_opportunities=mock_search_opportunities,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    queryables=MyProductQueryables,
    opportunity_properties=MyOpportunityProperties,
    order_parameters=MyOrderParameters,
    conforms_to=[PRODUCT.opportunities],
)


def create_mock_opportunity() -> AnyOpportunity:
    now = datetime.now(UTC)  # Use timezone-aware datetime
    start = now
    end = start + timedelta(days=5)

    # Create a list of mock opportunities for the given product
    return Opportunity(
        id=str(uuid4()),
        type="Feature",
        geometry=Point(
            type="Point",
            coordinates=Position2D(longitude=0.0, latitude=0.0),
        ),
        properties=MyOpportunityProperties(
            product_id="xyz123",
            datetime=(start, end),
            off_nadir=OffNadirRange(minimum=20, maximum=22),
            vehicle_id=[1],
            platform="platform_id",
            other_thing="abcd1234",  # type: ignore
        ),
    )


def pagination_tester(
    stapi_client: TestClient,
    url: str,
    method: str,
    limit: int,
    target: str,
    expected_returns: list[dict[str, Any]],
    body: dict[str, Any] | None = None,
) -> None:
    retrieved: list[dict[str, Any]] = []

    res = make_request(stapi_client, url, method, body, limit)
    assert res.status_code == status.HTTP_200_OK
    resp_body = res.json()

    assert len(resp_body[target]) <= limit
    retrieved.extend(resp_body[target])
    next_url = next((d["href"] for d in resp_body["links"] if d["rel"] == "next"), None)

    while next_url:
        if method == "POST":
            body = next((d["body"] for d in resp_body["links"] if d["rel"] == "next"), None)

        res = make_request(stapi_client, next_url, method, body, limit)

        assert res.status_code == status.HTTP_200_OK, res.status_code
        assert len(resp_body[target]) <= limit

        resp_body = res.json()
        retrieved.extend(resp_body[target])

        # get url w/ query params for next call if exists, and POST body if necessary
        if resp_body["links"]:
            next_url = next((d["href"] for d in resp_body["links"] if d["rel"] == "next"), None)
        else:
            next_url = None

    assert len(retrieved) == len(expected_returns)
    assert retrieved == expected_returns


def make_request(
    stapi_client: TestClient,
    url: str,
    method: str,
    body: dict[str, Any] | None,
    limit: int,
) -> Response:
    """request wrapper for pagination tests"""

    match method:
        case "GET":
            o = urlparse(url)
            base_url = f"{o.scheme}://{o.netloc}{o.path}"
            parsed_qs = parse_qs(o.query)
            params: dict[str, Any] = {}
            if "next" in parsed_qs:
                params["next"] = parsed_qs["next"][0]
            params["limit"] = int(parsed_qs.get("limit", [None])[0] or limit)
            res = stapi_client.get(base_url, params=params)
        case "POST":
            res = stapi_client.post(url, json=body)
        case _:
            fail(f"method {method} not supported in make request")

    return res
