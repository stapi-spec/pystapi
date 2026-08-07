from typing import Any

import pydantic
import pytest
from geojson_pydantic.geometries import Point
from stapi_pydantic import (
    Opportunity,
    OpportunityCollection,
    OpportunityProperties,
    OpportunityRequest,
    OpportunitySearchRecord,
    OpportunitySearchRecordCollection,
    OpportunitySearchStatus,
    OpportunitySearchStatusCollection,
    OrderParameters,
    OrderRequest,
)

SEARCH_PARAMS = {
    "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
}


def test_opportunity_search_status_accepts_extension_status_code() -> None:
    status = OpportunitySearchStatus.model_validate({"timestamp": "2024-04-10T09:15:00Z", "status_code": "queued"})
    assert status.status_code == "queued"
    assert status.model_dump(mode="json")["status_code"] == "queued"


def test_opportunity_search_status_code_constrainable_with_custom_enum() -> None:
    from enum import StrEnum

    class NarrowCodes(StrEnum):
        special = "special"

    with pytest.raises(pydantic.ValidationError):
        OpportunitySearchStatus[NarrowCodes].model_validate(
            {"timestamp": "2024-04-10T09:15:00Z", "status_code": "received"}
        )


def test_create_properties() -> None:
    _ = OpportunityProperties.model_validate(
        {"datetime": "2025-04-01T00:00:00Z/2025-04-01T23:59:59Z", "product_id": "foo"}
    )


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


SEARCH_RECORD_DICT = {
    "id": "search-1",
    "product_id": "umbra_spotlight",
    "search_parameters": SEARCH_PARAMS,
    "status": {
        "timestamp": "2024-04-18T11:00:00Z",
        "status_code": "received",
        "links": [],
    },
}


def test_opportunity_search_record_request_field() -> None:
    record = OpportunitySearchRecord.model_validate(SEARCH_RECORD_DICT)
    assert record.search_parameters.geometry.type == "Point"
    dumped = record.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunitySearchRecord"
    assert "opportunity_request" not in dumped


def test_opportunity_search_record_collection() -> None:
    collection = OpportunitySearchRecordCollection(records=[OpportunitySearchRecord.model_validate(SEARCH_RECORD_DICT)])
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunitySearchRecordCollection"
    assert len(dumped["records"]) == 1


def test_opportunity_search_status_collection() -> None:
    status = OpportunitySearchStatus.model_validate(SEARCH_RECORD_DICT["status"])
    collection = OpportunitySearchStatusCollection(statuses=[status])
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunitySearchStatusCollection"


def test_opportunity_collection_stapi_fields() -> None:
    collection: OpportunityCollection[Any, Any] = OpportunityCollection(features=[])
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunityCollection"
    assert dumped["stapi_version"] == "0.2.0"


OPPORTUNITY_DICT: dict[str, Any] = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
    "properties": {
        "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
        "product_id": "umbra_spotlight",
    },
}


def test_opportunity_bbox_3d_geometry() -> None:
    opportunity_dict: dict[str, Any] = {
        **OPPORTUNITY_DICT,
        "geometry": {
            "type": "LineString",
            "coordinates": [[13.0, 52.0, 10.0], [14.0, 53.0, 200.0]],
        },
    }
    opportunity: Opportunity[Any, Any] = Opportunity.model_validate(opportunity_dict)
    assert opportunity.model_dump(mode="json")["bbox"] == [13.0, 52.0, 10.0, 14.0, 53.0, 200.0]


def test_opportunity_serialization_schema_marks_spec_required_fields() -> None:
    schema = Opportunity[Point, OpportunityProperties].model_json_schema(mode="serialization")
    assert {"type", "stapi_type", "stapi_version", "links", "bbox"} <= set(schema["required"])
    assert {"type": "null"} not in schema["properties"]["bbox"].get("anyOf", [])


def test_opportunity_bbox_is_optional_to_supply_but_always_emitted() -> None:
    """Validation and serialization differ on bbox: a caller may omit it (the
    before-validator derives it), but a response always carries it, and neither
    mode may permit null.
    """
    validation = Opportunity.model_json_schema(mode="validation")
    serialization = Opportunity.model_json_schema(mode="serialization")

    assert "bbox" not in validation["required"]
    assert "bbox" in serialization["required"]
    for schema in (validation, serialization):
        assert "null" not in str(schema["properties"]["bbox"]).lower()


def test_opportunity_bbox_may_still_be_omitted_by_callers() -> None:
    # the before-validator supplies bbox, so declaring it required costs
    # callers nothing
    model = Opportunity[Point, OpportunityProperties]
    assert model.model_validate(OPPORTUNITY_DICT).bbox == (13.4, 52.5, 13.4, 52.5)
    assert model(**OPPORTUNITY_DICT).bbox == (13.4, 52.5, 13.4, 52.5)


def test_opportunity_collection_bbox_is_none_for_empty_features() -> None:
    # union_bboxes returns None for an empty sequence; assigning that back into
    # bbox re-triggers the validator under validate_assignment, unbounded
    class ValidatedOnAssignment(OpportunityCollection[Point, OpportunityProperties]):
        model_config = pydantic.ConfigDict(validate_assignment=True)

    assert OpportunityCollection(features=[]).bbox is None
    assert ValidatedOnAssignment(features=[]).bbox is None


def test_opportunity_collection_bbox_unions_features() -> None:
    model = Opportunity[Point, OpportunityProperties]
    other = {**OPPORTUNITY_DICT, "geometry": {"type": "Point", "coordinates": [14.4, 53.5]}}
    collection = OpportunityCollection[Point, OpportunityProperties](
        features=[model.model_validate(OPPORTUNITY_DICT), model.model_validate(other)]
    )
    assert collection.bbox == (13.4, 52.5, 14.4, 53.5)


def test_opportunity_id_is_string_only() -> None:
    schema = Opportunity[Point, OpportunityProperties].model_json_schema(mode="validation")
    id_types = {member.get("type") for member in schema["properties"]["id"].get("anyOf", [])}
    assert "integer" not in id_types


def test_opportunity_collection_omits_null_id() -> None:
    collection: OpportunityCollection[Any, Any] = OpportunityCollection(features=[])
    assert "id" not in collection.model_dump(mode="json")
    assert '"id":null' not in collection.model_dump_json()


def test_opportunity_collection_number_matched() -> None:
    collection: OpportunityCollection[Any, Any] = OpportunityCollection(features=[], number_matched=3)
    assert collection.model_dump(mode="json")["numberMatched"] == 3
    assert "numberMatched" not in OpportunityCollection(features=[]).model_dump(mode="json")


def test_search_record_collection_number_matched() -> None:
    collection = OpportunitySearchRecordCollection(records=[], number_matched=0)
    assert collection.model_dump(mode="json")["numberMatched"] == 0


def test_opportunity_geometry_required_non_null() -> None:
    with pytest.raises(pydantic.ValidationError):
        Opportunity[Point, OpportunityProperties].model_validate(
            {
                **OPPORTUNITY_DICT,
                "geometry": None,
            }
        )


def test_opportunity_properties_required() -> None:
    with pytest.raises(pydantic.ValidationError):
        Opportunity[Point, OpportunityProperties].model_validate(
            {
                **OPPORTUNITY_DICT,
                "properties": None,
            }
        )
