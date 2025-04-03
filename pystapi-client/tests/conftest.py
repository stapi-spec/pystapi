import json
from collections.abc import Generator
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from httpx import Response

WORKING_DIR = Path(__file__).parent


def load_fixture(name: str) -> dict[str, Any]:
    with open(WORKING_DIR / "fixtures" / f"{name}.json") as f:
        return json.load(f)  # type: ignore[no-any-return]


@pytest.fixture
def mocked_api() -> Generator[respx.MockRouter, None, None]:
    landing_page_data = load_fixture("landing_page")
    products = load_fixture("products")

    with respx.mock(base_url="https://stapi.example.com", assert_all_called=False) as respx_mock:
        landing_page = respx_mock.get("/")
        landing_page.return_value = Response(200, json=landing_page_data)

        conformance_route = respx_mock.get("/conformance")
        conformance_route.return_value = Response(200, json={"conformsTo": landing_page_data["conformsTo"]})

        # products_route.return_value = Response(200, json=products)

        def mock_products_response(request: httpx.Request) -> httpx.Response:
            products_limited = deepcopy(products)
            limit = request.url.params.get("limit")
            page = int(request.url.params.get("page", 1))
            if limit is not None:
                start_index = (page - 1) * int(limit)
                end_index = start_index + int(limit)
                products_limited["products"] = products_limited["products"][start_index:end_index]
                has_next_page = end_index < len(products_limited["products"]) + 1
                if has_next_page:
                    products_limited["links"].append(
                        {
                            "href": "https://stapi.example.com/products?limit=1&page=2",
                            "method": "GET",
                            "rel": "next",
                        }
                    )
            return Response(200, json=products_limited)

        respx_mock.get("/products").mock(side_effect=mock_products_response)
        respx_mock.get("/products", params={"limit": 1}).mock(side_effect=mock_products_response)

        yield respx_mock
