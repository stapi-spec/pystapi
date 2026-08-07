import datetime

import pydantic
import pytest
from stapi_pydantic import BaseOrderParameters, OrderParameters, OrderStatus, OrderStatusCode


def test_order_status_new() -> None:
    status = OrderStatus.new(OrderStatusCode.accepted)
    assert status.timestamp.tzinfo == datetime.UTC
    assert status.status_code == OrderStatusCode.accepted
    assert status.reason_code is None
    assert status.reason_text is None
    assert status.links == []


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
