from typing import Any

import pytest
import stapi_pydantic
from pydantic import BaseModel
from stapi_pydantic import (
    Conformance,
    Link,
    OpportunityCollection,
    OrderCollection,
    Product,
    Provider,
    RootResponse,
)


def test_link_serialization_schema_is_structured() -> None:
    schema = Link.model_json_schema(mode="serialization")
    assert {"href", "rel"} <= set(schema["required"])
    assert "href" in schema["properties"]


def test_link_json_dump_omits_none_fields() -> None:
    link = Link(href="https://example.com/orders/1", rel="self")
    dumped = link.model_dump(mode="json")
    assert dumped["rel"] == "self"
    assert "title" not in dumped
    assert "body" not in dumped


def test_link_preserves_extra_fields() -> None:
    link = Link.model_validate({"href": "https://example.com", "rel": "self", "vendor:hint": "x"})
    assert link.model_dump(mode="json")["vendor:hint"] == "x"


def test_root_response_serialization_schema_marks_spec_required_fields() -> None:
    schema = RootResponse.model_json_schema(mode="serialization")
    assert {"id", "conformsTo", "description", "links"} <= set(schema["required"])


def test_conformance_serialization_schema_requires_conforms_to() -> None:
    schema = Conformance.model_json_schema(mode="serialization", by_alias=True)
    assert "conformsTo" in schema.get("required", [])


def test_conformance_dumps_by_alias() -> None:
    # Conformance is nested in responses, and model config is not inherited by
    # nested models, so it has to serialize by alias itself.
    assert Conformance(conforms_to=["a"]).model_dump(mode="json") == {"conformsTo": ["a"]}
    assert Conformance(conforms_to=["a"]).model_dump() == {"conformsTo": ["a"]}


#: Models whose spec-OPTIONAL fields must be omitted rather than published as
#: null, and so must not appear in the serialization-required set.
OMIT_WHEN_UNSET = [
    (Link, {"href": "https://example.test", "rel": "self"}, {"type", "title", "method", "headers", "body"}),
    (Provider, {"name": "n"}, {"description", "roles", "url"}),
    # conformsTo is spec-REQUIRED on a Product, so it is always published and
    # is deliberately not in this set.
    (
        Product,
        {"id": "p", "description": "d", "license": "proprietary"},
        {"title", "keywords", "providers"},
    ),
    (RootResponse, {"id": "x", "description": "d"}, {"title"}),
]


@pytest.mark.parametrize(("model", "minimal", "optional"), OMIT_WHEN_UNSET, ids=lambda v: getattr(v, "__name__", ""))
def test_unset_optional_fields_are_omitted_not_published_as_null(
    model: type[BaseModel], minimal: dict[str, Any], optional: set[str]
) -> None:
    """A spec-OPTIONAL field is absent when unset, and so is not required."""
    dumped = model(**minimal).model_dump(mode="json")
    assert optional.isdisjoint(dumped), f"unset optional fields present: {sorted(optional & set(dumped))}"

    schema = model.model_json_schema(mode="serialization")
    assert optional.isdisjoint(schema.get("required", []))


@pytest.mark.parametrize("model", [OrderCollection, OpportunityCollection], ids=lambda m: m.__name__)
def test_collection_bbox_is_omitted_when_there_is_no_extent(model: type[BaseModel]) -> None:
    """A collection bbox is absent when unknown, not null, which is also what
    keeps it out of the serialization-required set.
    """
    assert "bbox" not in model(features=[]).model_dump(mode="json")
    for mode in ("validation", "serialization"):
        assert "bbox" not in model.model_json_schema(mode=mode).get("required", [])


#: Models whose spec-OPTIONAL fields must be omitted rather than published as
#: null, and so must not appear in the serialization-required set.


def _number_matched_collections() -> list[tuple[type[BaseModel], dict[str, Any]]]:
    """Every exported model carrying the shared NumberMatched field.

    Discovered rather than listed, so a collection added later cannot quietly
    escape the checks below.
    """
    discovered: list[tuple[type[BaseModel], dict[str, Any]]] = []
    seen: set[int] = set()
    for name in stapi_pydantic.__all__:
        model = getattr(stapi_pydantic, name)
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            continue
        if "number_matched" not in model.model_fields:
            continue
        # Deduplicate by identity, not by name: a deprecated alias exports the
        # same class twice and would otherwise be parametrized twice.
        if id(model) in seen:
            continue
        seen.add(id(model))
        required = [field for field, info in model.model_fields.items() if info.is_required()]
        discovered.append((model, dict.fromkeys(required, [])))
    return discovered


NUMBER_MATCHED_COLLECTIONS = _number_matched_collections()


def test_number_matched_collections_were_discovered() -> None:
    """Guard the discovery above: a bug there would silently parametrize nothing."""
    assert len(NUMBER_MATCHED_COLLECTIONS) >= 6
    assert all(payload for _, payload in NUMBER_MATCHED_COLLECTIONS)


def test_every_aliased_model_dumps_by_alias() -> None:
    # a model that declares an alias but does not dump by it emits field names
    # that contradict its own published schema whenever it is dumped outside a
    # by-alias context (e.g. nested in another model)
    offenders: list[str] = []
    checked: list[str] = []
    for name in stapi_pydantic.__all__:
        model = getattr(stapi_pydantic, name)
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            continue
        for field_name, field in model.model_fields.items():
            alias = field.serialization_alias or field.alias
            if alias is None or alias == field_name:
                continue
            # model_construct builds the model without knowing its required
            # fields; the placeholder value keeps `exclude_if` from omitting the
            # aliased field before it can be checked.
            placeholder: dict[str, Any] = {field_name: 1}
            dumped = model.model_construct(**placeholder).model_dump(warnings=False)
            checked.append(f"{model.__name__}.{field_name}")
            if alias not in dumped or field_name in dumped:
                offenders.append(f"{model.__name__}.{field_name}")
    assert offenders == []
    # guard the discovery: a bug there would check nothing and still pass
    assert {"Conformance.conforms_to", "Product.type_", "ProductCollection.number_matched"} <= set(checked)


@pytest.mark.parametrize(("model", "payload"), NUMBER_MATCHED_COLLECTIONS, ids=lambda v: getattr(v, "__name__", ""))
def test_number_matched_round_trips_under_wire_name(model: type[BaseModel], payload: dict[str, Any]) -> None:
    collection = model.model_validate({**payload, "links": [], "numberMatched": 7})
    assert collection.number_matched == 7  # type: ignore[attr-defined]
    assert collection.model_dump(mode="json")["numberMatched"] == 7
    assert collection.model_dump()["numberMatched"] == 7


@pytest.mark.parametrize(("model", "payload"), NUMBER_MATCHED_COLLECTIONS, ids=lambda v: getattr(v, "__name__", ""))
def test_number_matched_accepts_field_name_and_is_omitted_when_unset(
    model: type[BaseModel], payload: dict[str, Any]
) -> None:
    assert model.model_validate({**payload, "number_matched": 7}).number_matched == 7  # type: ignore[attr-defined]
    assert "numberMatched" not in model.model_validate(payload).model_dump(mode="json")


@pytest.mark.parametrize(("model", "payload"), NUMBER_MATCHED_COLLECTIONS, ids=lambda v: getattr(v, "__name__", ""))
def test_number_matched_stays_optional_and_aliased_in_json_schema(
    model: type[BaseModel], payload: dict[str, Any]
) -> None:
    validation = model.model_json_schema(mode="validation")
    assert "numberMatched" in validation["properties"]
    assert "numberMatched" not in validation.get("required", [])

    serialization = model.model_json_schema(mode="serialization")
    assert "numberMatched" in serialization["properties"]
    assert "numberMatched" not in serialization.get("required", [])
