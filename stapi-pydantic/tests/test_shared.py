from typing import Any

import pytest
from pydantic import BaseModel
from stapi_pydantic import (
    Conformance,
    Link,
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
