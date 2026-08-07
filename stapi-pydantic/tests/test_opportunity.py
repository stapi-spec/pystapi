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
    "status": {"timestamp": "2024-04-10T09:15:00Z", "status_code": "received"},
}


def test_opportunity_search_record_request_field() -> None:
    """A record says what was searched for, not which request body carried it."""
    record = OpportunitySearchRecord.model_validate(SEARCH_RECORD_DICT)
    assert record.search_parameters.geometry.type == "Point"
    dumped = record.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunitySearchRecord"
    assert "opportunity_request" not in dumped


def test_opportunity_search_record_collection() -> None:
    collection = OpportunitySearchRecordCollection.model_validate(
        {"records": [SEARCH_RECORD_DICT]},
    )
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunitySearchRecordCollection"
    assert len(dumped["records"]) == 1


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


def test_opportunity_search_status_collection() -> None:
    collection = OpportunitySearchStatusCollection.model_validate(
        {"statuses": [{"timestamp": "2024-04-10T09:15:00Z", "status_code": "received"}]}
    )
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "OpportunitySearchStatusCollection"
    assert len(dumped["statuses"]) == 1


OPPORTUNITY_DICT = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
    "properties": {
        "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
        "product_id": "umbra_spotlight",
    },
}


def test_opportunity_id_is_string_only() -> None:
    opportunity = Opportunity[Point, OpportunityProperties].model_validate({**OPPORTUNITY_DICT, "id": "opp-1"})
    assert opportunity.id == "opp-1"
    with pytest.raises(pydantic.ValidationError):
        Opportunity[Point, OpportunityProperties].model_validate({**OPPORTUNITY_DICT, "id": 1})


def test_opportunity_collection_omits_null_id() -> None:
    collection = OpportunityCollection[Point, OpportunityProperties].model_validate(
        {"type": "FeatureCollection", "features": []}
    )
    assert "id" not in collection.model_dump(mode="json")


def test_opportunity_geometry_required_non_null() -> None:
    """Feature types geometry as nullable, which would let a spec-violating
    response validate and dump.
    """
    with pytest.raises(pydantic.ValidationError):
        Opportunity[Point, OpportunityProperties].model_validate({**OPPORTUNITY_DICT, "geometry": None})


def test_opportunity_properties_required() -> None:
    with pytest.raises(pydantic.ValidationError):
        Opportunity[Point, OpportunityProperties].model_validate({**OPPORTUNITY_DICT, "properties": None})
