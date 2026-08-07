from stapi_pydantic import (
    OpportunityRequest,
    OrderParameters,
    OrderRequest,
)

SEARCH_PARAMS = {
    "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
}


def test_opportunity_request_shape() -> None:
    """An unspecified page size stays unspecified: the default is the server's to
    choose, not the model's.
    """
    req = OpportunityRequest.model_validate({"search_parameters": SEARCH_PARAMS})
    assert req.limit is None
    assert req.next is None


def test_opportunity_request_search_body_is_order_request_shaped() -> None:
    req = OpportunityRequest.model_validate({"search_parameters": SEARCH_PARAMS})
    body = req.search_body()
    assert set(body) == {"search_parameters"}
    assert body["search_parameters"]["geometry"]["type"] == "Point"


def test_search_body_is_valid_order_request() -> None:
    req = OpportunityRequest.model_validate({"search_parameters": SEARCH_PARAMS})
    order_request = OrderRequest[OrderParameters].model_validate(req.search_body())
    assert order_request.search_parameters == req.search_parameters


def test_opportunity_request_body_includes_pagination() -> None:
    req = OpportunityRequest.model_validate({"search_parameters": SEARCH_PARAMS, "next": "abc", "limit": 5})
    body = req.body()
    assert body["next"] == "abc"
    assert body["limit"] == 5
    assert "search_parameters" in body
