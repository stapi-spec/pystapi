import datetime

from stapi_pydantic import OrderStatus, OrderStatusCode


def test_order_status_new() -> None:
    status = OrderStatus.new(OrderStatusCode.accepted)
    assert status.timestamp.tzinfo == datetime.UTC
    assert status.status_code == OrderStatusCode.accepted
    assert status.reason_code is None
    assert status.reason_text is None
    assert status.links == []
