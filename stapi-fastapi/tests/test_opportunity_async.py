from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from stapi_fastapi.conformance import API, PRODUCT
from stapi_pydantic import (
    Link,
    OpportunityCollection,
    OpportunitySearchRecord,
    OpportunitySearchStatus,
    OpportunitySearchStatusCode,
)

from .backends import (
    mock_get_opportunity_search_record_statuses,
)
from .shared import (
    create_mock_opportunity,
    find_link,
    pagination_tester,
    product_test_spotlight,
    product_test_spotlight_async_opportunity,
    product_test_spotlight_sync_async_opportunity,
    product_test_spotlight_sync_opportunity,
)


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_monitor_link_present_on_search_records(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
    url_for: Callable[[str], str],
) -> None:
    client = stapi_client_async_opportunity
    product_id = "test-spotlight"

    # 201 create
    create_res = client.post(f"/products/{product_id}/opportunities", json=opportunity_search)
    assert create_res.status_code == 201
    create_body = create_res.json()
    record_id = create_body["id"]
    statuses_href = url_for(f"/searches/opportunities/{record_id}/statuses")

    monitor = find_link(create_body["links"], "monitor")
    assert monitor
    assert monitor["href"] == statuses_href

    # GET single record
    get_res = client.get(f"/searches/opportunities/{record_id}")
    assert get_res.status_code == 200
    get_monitor = find_link(get_res.json()["links"], "monitor")
    assert get_monitor
    assert get_monitor["href"] == statuses_href

    # GET record list
    list_res = client.get("/searches/opportunities")
    assert list_res.status_code == 200
    record = next(r for r in list_res.json()["records"] if r["id"] == record_id)
    list_monitor = find_link(record["links"], "monitor")
    assert list_monitor
    assert list_monitor["href"] == statuses_href


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
@pytest.mark.root_router_kwargs({"get_opportunity_search_record_statuses": None})
def test_monitor_link_absent_without_statuses_backend(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    client = stapi_client_async_opportunity
    product_id = "test-spotlight"

    create_res = client.post(f"/products/{product_id}/opportunities", json=opportunity_search)
    assert create_res.status_code == 201
    record_id = create_res.json()["id"]
    assert find_link(create_res.json()["links"], "monitor") is None

    get_res = client.get(f"/searches/opportunities/{record_id}")
    assert find_link(get_res.json()["links"], "monitor") is None

    list_res = client.get("/searches/opportunities")
    record = next(r for r in list_res.json()["records"] if r["id"] == record_id)
    assert find_link(record["links"], "monitor") is None


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_openapi_async_search_201_metadata(stapi_client_async_opportunity: TestClient) -> None:
    from stapi_fastapi.constants import TYPE_JSON

    # TestClient types `app` as the bare ASGI callable; the fixture always
    # builds a FastAPI app, which is what exposes `openapi()`.
    spec = cast(FastAPI, stapi_client_async_opportunity.app).openapi()
    responses = spec["paths"]["/products/test-spotlight/opportunities"]["post"]["responses"]

    # 201 documents the OpportunitySearchRecord as application/json (not geo+json)
    r201 = responses["201"]
    assert set(r201["content"].keys()) == {TYPE_JSON}
    assert r201["content"][TYPE_JSON]["schema"]["$ref"].endswith("/OpportunitySearchRecord")
    # Location header documented
    assert "Location" in r201["headers"]

    # This product cannot search synchronously, so it can only ever answer 201.
    # Documenting a 200 OpportunityCollection would promise a response that no
    # request to this deployment can elicit.
    assert "200" not in responses


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_openapi_create_order_201_location_header(stapi_client_async_opportunity: TestClient) -> None:
    from stapi_fastapi.constants import TYPE_GEOJSON

    spec = cast(FastAPI, stapi_client_async_opportunity.app).openapi()
    r201 = spec["paths"]["/products/test-spotlight/orders"]["post"]["responses"]["201"]
    assert "Location" in r201["headers"]
    # Order is GeoJSON, content stays geo+json
    assert set(r201["content"].keys()) == {TYPE_GEOJSON}


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_statuses_unknown_id_returns_404(
    stapi_client_async_opportunity: TestClient,
) -> None:
    res = stapi_client_async_opportunity.get("/searches/opportunities/does-not-exist/statuses")
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
@pytest.mark.root_router_kwargs(
    {
        # A statuses backend is supplied but the async search record backends
        # are withheld, so the statuses route must not be registered and its
        # conformance must be absent.
        "get_opportunity_search_records": None,
        "get_opportunity_search_record": None,
        "get_opportunity_search_record_statuses": mock_get_opportunity_search_record_statuses,
        "conformances": [API.core],
    }
)
def test_statuses_endpoint_gated_on_async_support(stapi_client_async_opportunity: TestClient) -> None:
    res = stapi_client_async_opportunity.get("/searches/opportunities/anything/statuses")
    assert res.status_code == status.HTTP_404_NOT_FOUND

    conformance = stapi_client_async_opportunity.get("/conformance").json()["conformsTo"]
    assert API.searches_opportunity_statuses not in conformance


@pytest.mark.mock_products([product_test_spotlight])
def test_no_opportunity_search_advertised(stapi_client: TestClient) -> None:
    product_id = "test-spotlight"

    # the `/products/{productId}/opportunities link should not be advertised on the product
    product_response = stapi_client.get(f"/products/{product_id}")
    product_body = product_response.json()
    assert find_link(product_body["links"], "opportunities") is None

    # the `searches/opportunities` link should not be advertised on the root
    root_response = stapi_client.get("/")
    root_body = root_response.json()
    assert find_link(root_body["links"], "search-records") is None


@pytest.mark.mock_products([product_test_spotlight_sync_opportunity])
def test_only_sync_search_advertised(stapi_client: TestClient) -> None:
    product_id = "test-spotlight"

    # the `/products/{productId}/opportunities link should be advertised on the product
    product_response = stapi_client.get(f"/products/{product_id}")
    product_body = product_response.json()
    assert find_link(product_body["links"], "opportunities")

    # the `searches/opportunities` link should not be advertised on the root
    root_response = stapi_client.get("/")
    root_body = root_response.json()
    assert find_link(root_body["links"], "search-records") is None


# test async search offered
@pytest.mark.parametrize(
    "mock_products",
    [
        [product_test_spotlight_async_opportunity],
        [product_test_spotlight_sync_async_opportunity],
    ],
)
def test_async_search_advertised(stapi_client_async_opportunity: TestClient) -> None:
    product_id = "test-spotlight"

    # the `/products/{productId}/opportunities link should be advertised on the product
    product_response = stapi_client_async_opportunity.get(f"/products/{product_id}")
    product_body = product_response.json()
    assert find_link(product_body["links"], "opportunities")

    # the `searches/opportunities` link should be advertised on the root
    root_response = stapi_client_async_opportunity.get("/")
    root_body = root_response.json()
    assert find_link(root_body["links"], "search-records")


@pytest.mark.mock_products([product_test_spotlight_sync_opportunity])
def test_sync_only_product_conformance(stapi_client: TestClient) -> None:
    product_id = "test-spotlight"
    res = stapi_client.get(f"/products/{product_id}/conformance")
    assert res.status_code == status.HTTP_200_OK
    conforms_to = res.json()["conformsTo"]
    assert PRODUCT.opportunities in conforms_to
    assert PRODUCT.opportunities_async not in conforms_to


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_async_only_product_conformance(stapi_client_async_opportunity: TestClient) -> None:
    product_id = "test-spotlight"
    res = stapi_client_async_opportunity.get(f"/products/{product_id}/conformance")
    assert res.status_code == status.HTTP_200_OK
    conforms_to = res.json()["conformsTo"]
    # async capability does not imply sync class
    assert PRODUCT.opportunities_async in conforms_to
    assert PRODUCT.opportunities not in conforms_to


@pytest.mark.mock_products([product_test_spotlight_sync_async_opportunity])
def test_sync_async_product_conformance(stapi_client_async_opportunity: TestClient) -> None:
    product_id = "test-spotlight"
    res = stapi_client_async_opportunity.get(f"/products/{product_id}/conformance")
    assert res.status_code == status.HTTP_200_OK
    conforms_to = res.json()["conformsTo"]
    assert PRODUCT.opportunities in conforms_to
    assert PRODUCT.opportunities_async in conforms_to


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_async_search_response(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"

    response = stapi_client_async_opportunity.post(url, json=opportunity_search)
    assert response.status_code == 201

    body = response.json()
    try:
        _ = OpportunitySearchRecord(**body)
    except Exception as _:
        pytest.fail("response is not an opportunity search record")

    assert find_link(body["links"], "self")


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_async_search_is_default(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"

    response = stapi_client_async_opportunity.post(url, json=opportunity_search)
    assert response.status_code == 201

    body = response.json()
    try:
        _ = OpportunitySearchRecord(**body)
    except Exception as _:
        pytest.fail("response is not an opportunity search record")


@pytest.mark.mock_products([product_test_spotlight_sync_async_opportunity])
def test_prefer_header(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"

    # prefer = "wait"
    response = stapi_client_async_opportunity.post(url, json=opportunity_search, headers={"Prefer": "wait"})
    assert response.status_code == 200
    assert response.headers["Preference-Applied"] == "wait"

    body = response.json()
    try:
        OpportunityCollection(**body)
    except Exception as _:
        pytest.fail("response is not an opportunity collection")

    # prefer = "respond-async"
    response = stapi_client_async_opportunity.post(url, json=opportunity_search, headers={"Prefer": "respond-async"})
    assert response.status_code == 201
    assert response.headers["Preference-Applied"] == "respond-async"

    body = response.json()
    try:
        OpportunitySearchRecord(**body)
    except Exception as _:
        pytest.fail("response is not an opportunity search record")


@pytest.mark.parametrize("prefer", ["respond-sync", "wait, respond-async", "WAIT", ""])
@pytest.mark.mock_products([product_test_spotlight_sync_async_opportunity])
def test_unsupported_prefer_header_is_rejected(
    prefer: str,
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    """A `Prefer` value outside the enum is a 400, as the published document promises."""
    res = stapi_client_async_opportunity.post(
        "/products/test-spotlight/opportunities",
        json=opportunity_search,
        headers={"Prefer": prefer},
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.mock_products([product_test_spotlight_sync_opportunity])
def test_unsupported_prefer_header_is_rejected_on_sync_only_product(
    stapi_client: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    """The check guards every opportunity search route, not just the async one."""
    res = stapi_client.post(
        "/products/test-spotlight/opportunities",
        json=opportunity_search,
        headers={"Prefer": "respond-sync"},
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.mock_products([product_test_spotlight_sync_async_opportunity])
def test_preference_applied_match_wait(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    # prefer=wait honored by a sync+async product -> wait applied
    url = "/products/test-spotlight/opportunities"
    res = stapi_client_async_opportunity.post(url, json=opportunity_search, headers={"Prefer": "wait"})
    assert res.status_code == 200
    assert res.headers["Preference-Applied"] == "wait"


@pytest.mark.mock_products([product_test_spotlight_sync_async_opportunity])
def test_preference_applied_match_respond_async(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    # prefer=respond-async honored by a sync+async product -> respond-async applied
    url = "/products/test-spotlight/opportunities"
    res = stapi_client_async_opportunity.post(url, json=opportunity_search, headers={"Prefer": "respond-async"})
    assert res.status_code == 201
    assert res.headers["Preference-Applied"] == "respond-async"


@pytest.mark.mock_products([product_test_spotlight_sync_opportunity])
def test_preference_applied_mismatch_respond_async_on_sync_only(
    stapi_client: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    # respond-async requested but product only supports sync -> wait applied
    url = "/products/test-spotlight/opportunities"
    res = stapi_client.post(url, json=opportunity_search, headers={"Prefer": "respond-async"})
    assert res.status_code == 200
    assert res.headers["Preference-Applied"] == "wait"


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_preference_applied_mismatch_wait_on_async_only(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    # wait requested but product only supports async -> respond-async applied
    url = "/products/test-spotlight/opportunities"
    res = stapi_client_async_opportunity.post(url, json=opportunity_search, headers={"Prefer": "wait"})
    assert res.status_code == 201
    assert res.headers["Preference-Applied"] == "respond-async"


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_async_search_record_retrieval(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    # post an async search
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"
    search_response = stapi_client_async_opportunity.post(url, json=opportunity_search)
    assert search_response.status_code == 201
    search_response_body = search_response.json()

    # get the search record by id and verify it matches the original response
    search_record_id = search_response_body["id"]
    record_response = stapi_client_async_opportunity.get(f"/searches/opportunities/{search_record_id}")
    assert record_response.status_code == 200
    record_response_body = record_response.json()
    assert record_response_body == search_response_body

    # verify the search record is in the list of all search records
    records_response = stapi_client_async_opportunity.get("/searches/opportunities")
    assert records_response.status_code == 200
    records_response_body = records_response.json()
    assert search_record_id in [x["id"] for x in records_response_body["records"]]


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_async_opportunity_search_to_completion(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
    url_for: Callable[[str], str],
) -> None:
    # Post a request for an async search
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"
    search_response = stapi_client_async_opportunity.post(url, json=opportunity_search)
    assert search_response.status_code == 201
    search_record = OpportunitySearchRecord(**search_response.json())

    # Simulate the search being completed by some external process:
    # - an OpportunityCollection is created and stored in the database
    collection = OpportunityCollection(
        id=str(uuid4()),
        features=[create_mock_opportunity()],
    )
    collection.links.append(
        Link(
            rel="create-order",
            href=url_for(f"/products/{product_id}/orders"),
            body=search_record.search_parameters.model_dump(),
            method="POST",
        )
    )
    collection.links.append(
        Link(
            rel="search-record",
            href=url_for(f"/searches/opportunities/{search_record.id}"),
        )
    )

    stapi_client_async_opportunity.app_state["_opportunities_db"].put_opportunity_collection(collection)

    # - the OpportunitySearchRecord links and status are updated in the database
    search_record.links.append(
        Link(
            rel="opportunities",
            href=url_for(f"/products/{product_id}/opportunities/{collection.id}"),
        )
    )
    search_record.status = OpportunitySearchStatus(
        timestamp=datetime.now(UTC),
        status_code=OpportunitySearchStatusCode.completed,
    )

    stapi_client_async_opportunity.app_state["_opportunities_db"].put_search_record(search_record)

    # Verify we can retrieve the OpportunitySearchRecord by its id and its status is
    # `completed`
    url = f"/searches/opportunities/{search_record.id}"
    retrieved_search_response = stapi_client_async_opportunity.get(url)
    assert retrieved_search_response.status_code == 200
    retrieved_search_record = OpportunitySearchRecord(**retrieved_search_response.json())
    assert retrieved_search_record.status.status_code == OpportunitySearchStatusCode.completed

    url = f"/searches/opportunities/{search_record.id}/statuses"
    retrieved_statuses_response = stapi_client_async_opportunity.get(url)
    assert retrieved_statuses_response.status_code == 200
    retrieved_statuses_body = retrieved_statuses_response.json()
    assert retrieved_statuses_body["stapi_type"] == "OpportunitySearchStatusCollection"
    retrieved_statuses = [OpportunitySearchStatus(**d) for d in retrieved_statuses_body["statuses"]]
    assert len(retrieved_statuses) >= 1
    assert retrieved_statuses[-1].status_code == OpportunitySearchStatusCode.completed

    # Verify we can retrieve the OpportunityCollection from the
    # OpportunitySearchRecord's `opportunities` link; verify the retrieved
    # OpportunityCollection contains an order link and a link pointing back to the
    # OpportunitySearchRecord
    opportunities_link = next(x for x in retrieved_search_record.links if x.rel == "opportunities")
    url = str(opportunities_link.href)
    retrieved_collection_response = stapi_client_async_opportunity.get(url)
    assert retrieved_collection_response.status_code == 200
    retrieved_collection = OpportunityCollection(**retrieved_collection_response.json())
    assert any(x for x in retrieved_collection.links if x.rel == "create-order")
    assert any(x for x in retrieved_collection.links if x.rel == "search-record")


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_new_search_location_header_matches_self_link(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"
    search_response = stapi_client_async_opportunity.post(url, json=opportunity_search)
    assert search_response.status_code == 201

    search_record = search_response.json()
    link = find_link(search_record["links"], "self")
    assert link
    assert search_response.headers["Location"] == str(link["href"])


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_bad_ids(stapi_client_async_opportunity: TestClient) -> None:
    search_record_id = "bad_id"
    res = stapi_client_async_opportunity.get(f"/searches/opportunities/{search_record_id}")
    assert res.status_code == status.HTTP_404_NOT_FOUND

    product_id = "test-spotlight"
    opportunity_collection_id = "bad_id"
    res = stapi_client_async_opportunity.get(f"/products/{product_id}/opportunities/{opportunity_collection_id}")
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.fixture
def setup_search_record_pagination(
    stapi_client_async_opportunity: TestClient,
    opportunity_search: dict[str, Any],
) -> list[dict[str, Any]]:
    product_id = "test-spotlight"
    search_records = []
    for _ in range(3):
        response = stapi_client_async_opportunity.post(f"/products/{product_id}/opportunities", json=opportunity_search)
        assert response.status_code == 201

        body = response.json()
        search_records.append(body)

    return search_records


@pytest.mark.parametrize("limit", [1, 2, 4])
@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_get_search_records_pagination(
    stapi_client_async_opportunity: TestClient,
    setup_search_record_pagination: list[dict[str, Any]],
    limit: int,
) -> None:
    expected_returns: list[dict[str, Any]] = setup_search_record_pagination

    pagination_tester(
        stapi_client=stapi_client_async_opportunity,
        url="/searches/opportunities",
        method="GET",
        limit=limit,
        target="records",
        expected_returns=expected_returns,
    )


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_async_search_rejects_missing_required_queryable_predicate(
    stapi_client_async_opportunity: TestClient,
) -> None:
    # test-spotlight's queryables model (MyProductQueryables) requires `off_nadir`;
    # omitting a filter predicate for it should be rejected before hitting the backend.
    product_id = "test-spotlight"
    response = stapi_client_async_opportunity.post(
        f"/products/{product_id}/opportunities",
        json={
            "search_parameters": {
                "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
                "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
            },
        },
    )
    assert response.status_code == 400
