import datetime
from typing import Any

import pydantic
import pytest
from stapi_pydantic import (
    BaseOrderParameters,
    Order,
    OrderParameters,
    OrderRequest,
    OrderStatus,
    OrderStatusCode,
    StoredOrderRequest,
)


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


ORDER_DICT: dict[str, Any] = {
    "id": "order-1",
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
    "properties": {
        "product_id": "umbra_spotlight",
        "created": "2024-04-10T09:15:00Z",
        "status": {
            "timestamp": "2024-04-10T09:15:00Z",
            "status_code": "received",
            "links": [],
        },
        "order_request": {"search_parameters": SEARCH_PARAMS},
        "owner": {"organization": "ACME"},
    },
}


def test_order_properties_order_request() -> None:
    order = Order[OrderStatus].model_validate(ORDER_DICT)
    assert order.properties.order_request.order_parameters == BaseOrderParameters()
    assert order.properties.status.status_code == OrderStatusCode.received


def test_stored_order_parameters_preserve_provider_fields() -> None:
    order_dict = {
        **ORDER_DICT,
        "properties": {
            **ORDER_DICT["properties"],
            "order_request": {
                "search_parameters": SEARCH_PARAMS,
                "order_parameters": {"deliveryFormat": "GEOTIFF"},
            },
        },
    }
    order = Order[OrderStatus].model_validate(order_dict)
    params = order.properties.order_request.order_parameters
    assert isinstance(params, BaseOrderParameters)
    assert params.model_dump()["deliveryFormat"] == "GEOTIFF"


def test_order_extra_properties_allowed() -> None:
    order = Order[OrderStatus].model_validate(ORDER_DICT)
    assert order.properties.model_dump()["owner"] == {"organization": "ACME"}


def test_stored_order_request_preserves_unknown_fields() -> None:
    stored = StoredOrderRequest.model_validate({"search_parameters": SEARCH_PARAMS, "provider_extra": 1})
    assert stored.model_dump()["provider_extra"] == 1


def test_search_parameters_preserve_unknown_fields() -> None:
    order = Order[OrderStatus].model_validate(
        {
            **ORDER_DICT,
            "properties": {
                **ORDER_DICT["properties"],
                "order_request": {"search_parameters": {**SEARCH_PARAMS, "vendor:priority": "high"}},
            },
        }
    )
    dumped = order.model_dump(mode="json")
    assert dumped["properties"]["order_request"]["search_parameters"]["vendor:priority"] == "high"
