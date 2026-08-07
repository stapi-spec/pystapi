from stapi_pydantic import Link


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
