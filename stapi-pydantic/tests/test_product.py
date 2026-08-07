import pydantic
import pytest
from stapi_pydantic import Product, ProductCollection


def test_products_collection_stapi_fields() -> None:
    collection = ProductCollection(products=[Product(id="p1", license="proprietary", description="d")])
    dumped = collection.model_dump(mode="json")
    assert dumped["stapi_type"] == "ProductCollection"
    assert dumped["stapi_version"] == "0.2.0"
    assert "type" not in dumped


def test_product_description_is_required() -> None:
    with pytest.raises(pydantic.ValidationError, match="description"):
        Product.model_validate({"id": "p1", "license": "proprietary"})


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


def test_products_collection_dumps_nested_product_by_alias() -> None:
    # model config is not inherited by nested models: the collection setting
    # serialize_by_alias does nothing for the products it contains.
    collection = ProductCollection(products=[Product(id="p1", license="proprietary", description="d")])
    assert collection.model_dump(mode="json")["products"][0]["type"] == "Collection"
    assert collection.model_dump()["products"][0]["type"] == "Collection"


def test_product_collection_is_named_for_its_stapi_type() -> None:
    assert ProductCollection.model_fields["stapi_type"].default == "ProductCollection"
