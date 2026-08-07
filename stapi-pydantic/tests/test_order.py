import datetime

import pydantic
import pytest
from stapi_pydantic import BaseOrderParameters, OrderParameters, OrderRequest, OrderStatus, OrderStatusCode


def test_order_status_new() -> None:
    status = OrderStatus.new(OrderStatusCode.accepted)
    assert status.timestamp.tzinfo == datetime.UTC
    assert status.status_code == OrderStatusCode.accepted
    assert status.reason_code is None
    assert status.reason_text is None
    assert status.links == []


SEARCH_PARAMS = {
    "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
}


class RequiredParams(OrderParameters):
    delivery_format: str


def test_concrete_order_parameters_are_base_order_parameters() -> None:
    assert isinstance(RequiredParams(delivery_format="GEOTIFF"), BaseOrderParameters)

    # RequiredParams (via OrderParameters) forbids extra fields...
    with pytest.raises(pydantic.ValidationError):
        RequiredParams.model_validate({"delivery_format": "GEOTIFF", "unexpected_field": "value"})

    # ...while BaseOrderParameters allows and preserves them.
    base = BaseOrderParameters.model_validate({"unexpected_field": "value"})
    assert base.model_dump()["unexpected_field"] == "value"


def test_order_request_shape() -> None:
    req = OrderRequest[OrderParameters].model_validate({"search_parameters": SEARCH_PARAMS, "order_parameters": {}})
    assert req.search_parameters.filter is None


def test_order_request_omitted_order_parameters_is_empty_object() -> None:
    req = OrderRequest[OrderParameters].model_validate({"search_parameters": SEARCH_PARAMS})
    assert req.order_parameters == OrderParameters()


def test_order_request_omitted_order_parameters_fails_when_required() -> None:
    with pytest.raises(pydantic.ValidationError):
        OrderRequest[RequiredParams].model_validate({"search_parameters": SEARCH_PARAMS})
