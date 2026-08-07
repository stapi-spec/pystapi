from stapi_pydantic import Product


def test_product_serialization_schema_marks_spec_required_fields() -> None:
    schema = Product.model_json_schema(mode="serialization")
    assert {"type", "stapi_type", "stapi_version", "id", "description", "license", "links"} <= set(schema["required"])


def test_product_dumps_type_by_alias() -> None:
    # `type` is required by Product's own serialization schema, so a bare dump
    # (not just FastAPI's by-alias response rendering) has to emit it.
    product = Product(id="p1", license="proprietary", description="d")
    assert product.model_dump(mode="json")["type"] == "Collection"
    assert product.model_dump()["type"] == "Collection"
    assert "type_" not in product.model_dump()
