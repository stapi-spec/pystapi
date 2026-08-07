import datetime
from enum import StrEnum
from typing import Any

import pydantic
import pytest
from stapi_pydantic import (
    BaseOrderParameters,
    Order,
    OrderCollection,
    OrderParameters,
    OrderRequest,
    OrderStatus,
    OrderStatusCode,
    StoredOrderRequest,
)

SEARCH_PARAMS = {
    "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
}


def test_order_status_new() -> None:
    status = OrderStatus.new(OrderStatusCode.accepted)
    assert status.timestamp.tzinfo == datetime.UTC
    assert status.status_code == OrderStatusCode.accepted
    assert status.reason_code is None
    assert status.reason_text is None
    assert status.links == []


def test_order_status_new_uses_cls() -> None:
    class NarrowCodes(StrEnum):
        special = "special"

    narrowed = OrderStatus[NarrowCodes]
    status = narrowed.new("special")
    assert type(status) is narrowed
    assert status.status_code is NarrowCodes.special

    # the parameterization is enforced rather than silently falling back to the
    # unparameterized OrderStatus
    with pytest.raises(pydantic.ValidationError):
        narrowed.new("received")


def test_order_status_accepts_extension_status_code() -> None:
    status = OrderStatus.model_validate({"timestamp": "2024-04-10T09:15:00Z", "status_code": "tasking_window_open"})
    assert status.status_code == "tasking_window_open"
    assert status.model_dump(mode="json")["status_code"] == "tasking_window_open"


def test_order_status_known_code_validates_to_enum() -> None:
    status = OrderStatus.model_validate({"timestamp": "2024-04-10T09:15:00Z", "status_code": "received"})
    assert status.status_code is OrderStatusCode.received


def test_order_status_code_constrainable_with_custom_enum() -> None:
    class NarrowCodes(StrEnum):
        special = "special"

    narrowed = OrderStatus[NarrowCodes]
    assert narrowed.model_validate({"timestamp": "2024-04-10T09:15:00Z", "status_code": "special"}).status_code is (
        NarrowCodes.special
    )
    with pytest.raises(pydantic.ValidationError):
        narrowed.model_validate({"timestamp": "2024-04-10T09:15:00Z", "status_code": "received"})


def test_order_status_code_schema_allows_extension_strings() -> None:
    status_code_schema = OrderStatus.model_json_schema()["properties"]["status_code"]
    assert {"type": "string"} in status_code_schema["anyOf"]
    assert any("$ref" in member for member in status_code_schema["anyOf"])


class RequiredParams(OrderParameters):
    delivery_format: str


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


def test_concrete_order_parameters_are_base_order_parameters() -> None:
    assert isinstance(RequiredParams(delivery_format="GEOTIFF"), BaseOrderParameters)

    # RequiredParams (via OrderParameters) forbids extra fields...
    with pytest.raises(pydantic.ValidationError):
        RequiredParams.model_validate({"delivery_format": "GEOTIFF", "unexpected_field": "value"})

    # ...while BaseOrderParameters allows and preserves them.
    base = BaseOrderParameters.model_validate({"unexpected_field": "value"})
    assert base.model_dump()["unexpected_field"] == "value"


def test_order_extra_properties_allowed() -> None:
    order = Order[OrderStatus].model_validate(ORDER_DICT)
    assert order.properties.model_dump()["owner"] == {"organization": "ACME"}


def test_order_bbox_computed_and_serialized() -> None:
    order = Order[OrderStatus].model_validate(ORDER_DICT)
    dumped = order.model_dump(mode="json")
    assert dumped["bbox"] == [13.4, 52.5, 13.4, 52.5]


def test_order_bbox_3d_geometry() -> None:
    order_dict: dict[str, Any] = {
        **ORDER_DICT,
        "geometry": {
            "type": "LineString",
            "coordinates": [[13.0, 52.0, 10.0], [14.0, 53.0, 200.0]],
        },
    }
    order = Order[OrderStatus].model_validate(order_dict)
    assert order.model_dump(mode="json")["bbox"] == [13.0, 52.0, 10.0, 14.0, 53.0, 200.0]


def test_order_serialization_schema_marks_spec_required_fields() -> None:
    schema = Order[OrderStatus].model_json_schema(mode="serialization")
    assert {"type", "stapi_type", "stapi_version", "links", "bbox"} <= set(schema["required"])


def test_order_bbox_serialization_schema_is_not_nullable() -> None:
    schema = Order[OrderStatus].model_json_schema(mode="serialization")
    bbox = schema["properties"]["bbox"]
    assert {"type": "null"} not in bbox.get("anyOf", [])


def test_order_bbox_is_optional_to_supply_but_always_emitted() -> None:
    """Validation and serialization differ on bbox: a caller may omit it (the
    before-validator derives it), but a response always carries it, and neither
    mode may permit null.
    """
    validation = Order[OrderStatus].model_json_schema(mode="validation")
    serialization = Order[OrderStatus].model_json_schema(mode="serialization")

    assert "bbox" not in validation["required"]
    assert "bbox" in serialization["required"]
    for schema in (validation, serialization):
        assert "null" not in str(schema["properties"]["bbox"]).lower()


def test_order_bbox_may_still_be_omitted_by_callers() -> None:
    # the before-validator supplies bbox, so declaring it required costs
    # callers nothing
    assert Order[OrderStatus].model_validate(ORDER_DICT).bbox == (13.4, 52.5, 13.4, 52.5)
    assert Order[OrderStatus](**ORDER_DICT).bbox == (13.4, 52.5, 13.4, 52.5)


def test_order_collection_bbox_is_none_for_empty_features() -> None:
    # union_bboxes returns None for an empty sequence; assigning that back into
    # bbox re-triggers the validator under validate_assignment, unbounded
    class ValidatedOnAssignment(OrderCollection[OrderStatus]):
        model_config = pydantic.ConfigDict(validate_assignment=True)

    assert OrderCollection[OrderStatus](features=[]).bbox is None
    assert ValidatedOnAssignment(features=[]).bbox is None


def test_order_collection_bbox_unions_features() -> None:
    other = {**ORDER_DICT, "id": "order-2", "geometry": {"type": "Point", "coordinates": [14.4, 53.5]}}
    collection = OrderCollection[OrderStatus](
        features=[Order[OrderStatus].model_validate(ORDER_DICT), Order[OrderStatus].model_validate(other)]
    )
    assert collection.bbox == (13.4, 52.5, 14.4, 53.5)


def _order_with(geometry: dict[str, Any], id_: str) -> Order[OrderStatus]:
    return Order[OrderStatus].model_validate({**ORDER_DICT, "id": id_, "geometry": geometry})


LINE_3D = {"type": "LineString", "coordinates": [[13.0, 52.0, 10.0], [16.0, 55.0, 200.0]]}
LINE_3D_LOWER = {"type": "LineString", "coordinates": [[12.0, 51.0, 5.0], [12.5, 51.5, 100.0]]}


def test_order_collection_bbox_unions_3d_features() -> None:
    collection = OrderCollection[OrderStatus](
        features=[_order_with(LINE_3D, "order-1"), _order_with(LINE_3D_LOWER, "order-2")]
    )
    assert collection.bbox == (12.0, 51.0, 5.0, 16.0, 55.0, 200.0)


def test_order_collection_bbox_degrades_to_2d_when_members_are_mixed() -> None:
    # elevation is unknown for the 2D member, so the union cannot claim one
    collection = OrderCollection[OrderStatus](
        features=[
            _order_with(LINE_3D, "order-1"),
            _order_with({"type": "Point", "coordinates": [12.0, 51.0]}, "order-2"),
        ]
    )
    assert collection.bbox == (12.0, 51.0, 16.0, 55.0)


def test_order_collection_number_matched_not_serialization_required() -> None:
    schema = OrderCollection[OrderStatus].model_json_schema(mode="serialization")
    assert {"type", "stapi_type", "stapi_version", "links", "features"} <= set(schema["required"])
    assert "numberMatched" not in schema["required"]


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


def test_order_empty_geometry_bbox_error_is_clear() -> None:
    with pytest.raises(pydantic.ValidationError, match="bbox"):
        Order[OrderStatus].model_validate({**ORDER_DICT, "geometry": {"type": "MultiPoint", "coordinates": []}})


def test_order_collection_stapi_fields() -> None:
    collection = OrderCollection[OrderStatus](features=[Order[OrderStatus].model_validate(ORDER_DICT)])
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "OrderCollection"
    assert dumped["stapi_version"] == "0.2.0"
