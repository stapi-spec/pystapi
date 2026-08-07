from typing import Any

import pytest
from fastapi.testclient import TestClient
from stapi_fastapi.query_params import MAX_LIMIT
from stapi_pydantic import (
    OpportunityCollection,
)

from .shared import AssertLink, create_mock_opportunity, pagination_tester


def test_search_opportunities_response(
    stapi_client: TestClient, assert_link: AssertLink, opportunity_search: dict[str, Any]
) -> None:
    product_id = "test-spotlight"
    url = f"/products/{product_id}/opportunities"

    response = stapi_client.post(url, json=opportunity_search)

    assert response.status_code == 200, f"Failed for product: {product_id}"
    body = response.json()

    # Validate the opportunity was returned
    assert len(body["features"]) == 1

    try:
        _ = OpportunityCollection(**body)
    except Exception as _:
        pytest.fail("response is not an opportunity collection")

    assert_link(
        f"POST {url}",
        body,
        "create-order",
        f"/products/{product_id}/orders",
        method="POST",
    )


@pytest.mark.parametrize("limit", [1, 2, 4])
def test_search_opportunities_pagination(
    limit: int,
    stapi_client: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    mock_pagination_opportunities = [create_mock_opportunity() for __ in range(3)]
    stapi_client.app_state["_opportunities"] = mock_pagination_opportunities
    product_id = "test-spotlight"
    expected_returns = [x.model_dump(mode="json") for x in mock_pagination_opportunities]

    pagination_tester(
        stapi_client=stapi_client,
        url=f"/products/{product_id}/opportunities",
        method="POST",
        limit=limit,
        target="features",
        expected_returns=expected_returns,
        body=opportunity_search,
    )


@pytest.mark.parametrize("limit", [0, -1])
def test_search_opportunities_rejects_limit_below_the_minimum(
    limit: int,
    stapi_client: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    """The POST body's `limit` is bounded exactly as the GET query param is."""
    response = stapi_client.post(
        "/products/test-spotlight/opportunities",
        json={**opportunity_search, "limit": limit},
    )
    # 422 is spelled out: starlette renamed its constant for this status code,
    # and the old name now raises a DeprecationWarning.
    assert response.status_code == 422


def test_search_opportunities_clamps_an_over_large_limit(
    stapi_client: TestClient,
    opportunity_search: dict[str, Any],
) -> None:
    """As on the GET collections: the spec's `limit` is a request, not a demand."""
    response = stapi_client.post(
        "/products/test-spotlight/opportunities",
        json={**opportunity_search, "limit": MAX_LIMIT + 1},
    )
    assert response.status_code == 200, response.text


def test_search_opportunities_rejects_missing_required_queryable_predicate(
    stapi_client: TestClient,
) -> None:
    # test-spotlight's queryables model (MyProductQueryables) requires `off_nadir`;
    # omitting a filter predicate for it should be rejected before hitting the backend.
    product_id = "test-spotlight"
    response = stapi_client.post(
        f"/products/{product_id}/opportunities",
        json={
            "search_parameters": {
                "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
                "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
            },
        },
    )
    assert response.status_code == 400
