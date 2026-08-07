import os
import subprocess
import sys
from typing import Any

from pystapi_schema_generator.application import (
    _HTTP_METHODS,
    _local_ref_slots,
    _merge_input_output_pairs,
    _rewrite_refs,
    _schema_name,
    export_openapi,
)
from stapi_fastapi.conformance import API
from stapi_pydantic import STAPI_VERSION

EXPECTED_PATHS = {
    "/",
    "/conformance",
    "/products",
    "/products/{productId}",
    "/products/{productId}/conformance",
    "/products/{productId}/queryables",
    "/products/{productId}/order-parameters",
    "/products/{productId}/orders",
    "/products/{productId}/opportunities",
    "/products/{productId}/opportunities/{opportunityCollectionId}",
    "/orders",
    "/orders/{orderId}",
    "/orders/{orderId}/statuses",
    "/searches/opportunities",
    "/searches/opportunities/{searchRecordId}",
    "/searches/opportunities/{searchRecordId}/statuses",
}

# Full inventory of the exported component schemas. Any silently dropped or
# renamed schema must fail here, guarding CI against upstream drift.
EXPECTED_SCHEMA_NAMES = {
    "BaseOrderParameters",
    "Conformance",
    "HTTPValidationError",
    "JsonSchema",
    "LineString",
    "Link",
    "MultiLineString",
    "MultiPoint",
    "MultiPolygon",
    "Opportunity",
    "OpportunityCollection",
    "OpportunityProperties",
    "OpportunityRequest",
    "OpportunitySearchRecord",
    "OpportunitySearchRecordCollection",
    "OpportunitySearchStatus",
    "OpportunitySearchStatusCode",
    "OpportunitySearchStatusCollection",
    "Order",
    "OrderCollection",
    "OrderParameters",
    "OrderProperties",
    "OrderRequest",
    "OrderStatus",
    "OrderStatusCode",
    "OrderStatusCollection",
    "Point",
    "Polygon",
    "Position2D",
    "Position3D",
    "Product",
    "ProductCollection",
    "Provider",
    "ProviderRole",
    "RootResponse",
    "SearchParameters",
    "StoredOrderRequest",
    "ValidationError",
}


def _operations(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        op
        for path_item in schema["paths"].values()
        for method, op in path_item.items()
        if method in _HTTP_METHODS and isinstance(op, dict)
    ]


def test_path_inventory_matches_spec_endpoints() -> None:
    assert set(export_openapi()["paths"]) == EXPECTED_PATHS


def test_schema_inventory_matches_snapshot() -> None:
    schemas = export_openapi()["components"]["schemas"]
    assert set(schemas) == EXPECTED_SCHEMA_NAMES


def test_no_concrete_example_product_leakage() -> None:
    """The concrete product id must not leak into any path, operationId, or
    schema key/title. It may still legitimately appear in prose descriptions
    and conformance URIs (example.com), so scope to identifiers only."""
    schema = export_openapi()

    for path in schema["paths"]:
        assert "example" not in path.lower(), f"leaked in path {path}"

    for op in _operations(schema):
        operation_id = op.get("operationId", "")
        assert "example" not in operation_id.lower(), f"leaked in operationId {operation_id}"

    for name, component in schema["components"]["schemas"].items():
        assert "example" not in name.lower(), f"leaked in schema name {name}"
        assert "example" not in component.get("title", "").lower(), f"leaked in title of {name}"


def test_operation_ids_are_clean_and_generic() -> None:
    schema = export_openapi()
    ids = {op["operationId"] for op in _operations(schema) if "operationId" in op}
    # Generic, readable ids for the core operations.
    assert {"get_product", "create_order", "search_opportunities"} <= ids
    # No FastAPI default mangling (router prefix + path + method).
    for operation_id in ids:
        assert "products_" not in operation_id
        assert not operation_id.startswith("root_")
    # All operationIds are unique.
    id_list = [op["operationId"] for op in _operations(schema) if "operationId" in op]
    assert len(id_list) == len(set(id_list))


def test_templated_operations_declare_product_id_param() -> None:
    schema = export_openapi()
    for path, ops in schema["paths"].items():
        if "{productId}" not in path:
            continue
        for op in ops.values():
            names = {p["name"] for p in op.get("parameters", []) if p.get("in") == "path"}
            assert "productId" in names, f"missing productId param on {path}"


def test_info_and_external_docs() -> None:
    schema = export_openapi()
    assert schema["info"]["title"] == "STAPI"
    assert schema["info"]["version"] == STAPI_VERSION
    assert schema["externalDocs"]["url"] == "https://stapi-spec.github.io/stapi-spec/"


# --- Exported document reflects the upstream model/router fixes -------------


def test_order_response_marks_spec_required_fields() -> None:
    order = export_openapi()["components"]["schemas"]["Order"]
    required = set(order.get("required", []))
    for field in ("stapi_type", "stapi_version", "type", "links", "bbox"):
        assert field in required, f"{field} not required on Order response"


def test_order_bbox_has_no_null_branch() -> None:
    order = export_openapi()["components"]["schemas"]["Order"]
    bbox = order["properties"]["bbox"]
    # bbox is non-nullable: the anyOf branches are the 2D/3D tuples, no null.
    assert "null" not in str(bbox).lower()
    for branch in bbox.get("anyOf", []):
        assert branch.get("type") != "null"


def test_no_required_property_is_nullable() -> None:
    """A required property must never permit null.

    `json_schema_serialization_defaults_required` marks every defaulted field as
    required, so an optional-and-nullable one needs `exclude_if` or it silently
    becomes wrongly required.
    """

    def is_nullable(prop: dict[str, Any]) -> bool:
        if prop.get("type") == "null":
            return True
        return any(branch.get("type") == "null" for branch in prop.get("anyOf", []))

    offenders = [
        f"{name}.{prop_name}"
        for name, schema in export_openapi()["components"]["schemas"].items()
        for prop_name in schema.get("required", [])
        if is_nullable(schema.get("properties", {}).get(prop_name, {}))
    ]
    assert not offenders, f"required properties that permit null: {sorted(offenders)}"


def test_create_order_201_documents_location_header() -> None:
    responses = export_openapi()["paths"]["/products/{productId}/orders"]["post"]["responses"]
    created = responses["201"]
    assert "Location" in created["headers"]
    assert "application/geo+json" in created["content"]


def test_async_search_201_is_json_only_with_location() -> None:
    responses = export_openapi()["paths"]["/products/{productId}/opportunities"]["post"]["responses"]
    created = responses["201"]
    assert set(created["content"]) == {"application/json"}
    assert "Location" in created["headers"]


def test_order_status_code_allows_arbitrary_strings() -> None:
    """The order status schema's status_code must accept arbitrary strings
    (anyOf of the enum and a bare string), not just the enum."""
    order_status = export_openapi()["components"]["schemas"]["OrderStatus"]
    status_code = order_status["properties"]["status_code"]
    branch_kinds = status_code.get("anyOf", [])
    has_enum = any("$ref" in b for b in branch_kinds)
    has_string = any(b.get("type") == "string" for b in branch_kinds)
    assert has_enum and has_string, status_code


# --- Cleaned document invariants -------------------------------------------


def test_no_orphan_base_model_component() -> None:
    """No pass drops this: the queryables endpoints return a `JsonSchema`, so no
    annotation names `BaseModel` for FastAPI to register."""
    schemas = export_openapi()["components"]["schemas"]
    assert "BaseModel" not in schemas


def test_all_component_schemas_are_referenced() -> None:
    schema = export_openapi()
    referenced: set[str] = set()

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            # via _local_ref_slots rather than the `$ref` key alone: a
            # `discriminator.mapping` names its targets as bare strings, and
            # every geometry field carries one.
            referenced.update(
                name for container, key in _local_ref_slots(node) if (name := _schema_name(container[key])) is not None
            )
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for item in node:
                collect(item)

    collect(schema["paths"])
    collect(schema["components"]["schemas"])
    orphans = set(schema["components"]["schemas"]) - referenced
    assert not orphans, f"unreferenced component schemas: {sorted(orphans)}"


def test_no_dangling_refs() -> None:
    schema = export_openapi()
    names = set(schema["components"]["schemas"])
    dangling: set[str] = set()

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                target = ref[len("#/components/schemas/") :]
                if target not in names:
                    dangling.add(target)
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for item in node:
                collect(item)

    collect(schema)
    assert not dangling, f"dangling $refs: {sorted(dangling)}"


def test_conformsto_carries_a_conformance_uri_example() -> None:
    """A document naming no conformance class leaves a reader nothing to
    recognize. The example comes from the models, so every deployment has one.
    """
    schemas = export_openapi()["components"]["schemas"]
    for name in ("RootResponse", "Conformance"):
        examples = schemas[name]["properties"]["conformsTo"].get("examples")
        assert examples, f"{name}.conformsTo has no example"
        assert API.core in examples[0]


def test_key_component_schemas_present() -> None:
    components = export_openapi()["components"]["schemas"]
    for name in (
        "StoredOrderRequest",
        "OrderStatusCollection",
        "OpportunitySearchRecordCollection",
        "OpportunitySearchStatusCollection",
    ):
        assert name in components


def test_export_is_deterministic() -> None:
    a: dict[str, Any] = export_openapi()
    b: dict[str, Any] = export_openapi()
    assert a == b


def test_export_is_deterministic_across_hash_seeds() -> None:
    """Run the console script in fresh subprocesses with different hash seeds
    and require byte-identical output."""

    def run(seed: str) -> bytes:
        result = subprocess.run(
            [sys.executable, "-m", "pystapi_schema_generator.application"],
            capture_output=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )
        return result.stdout

    assert run("0") == run("123456789")


def test_rewrite_refs_updates_discriminator_mappings() -> None:
    """Renames must follow ``discriminator.mapping``, whose values are bare ref
    strings a ``$ref``-only rewriter would leave pointing at the old name.
    """
    node: dict[str, Any] = {
        "oneOf": [{"$ref": "#/components/schemas/Old"}],
        "discriminator": {"propertyName": "type", "mapping": {"Old": "#/components/schemas/Old"}},
    }

    _rewrite_refs(node, {"Old": "New"})

    assert node["oneOf"][0]["$ref"] == "#/components/schemas/New"
    assert node["discriminator"]["mapping"]["Old"] == "#/components/schemas/New"


def test_local_ref_slots_sees_discriminator_mappings() -> None:
    """A reference held in a ``discriminator.mapping`` is a reference like any other."""
    node = {"discriminator": {"propertyName": "type", "mapping": {"Only": "#/components/schemas/Only"}}}

    found = {name for container, key in _local_ref_slots(node) if (name := _schema_name(container[key])) is not None}

    assert found == {"Only"}


def test_order_parameters_is_open_in_the_generic_document() -> None:
    """The published ``order_parameters`` schema must not forbid all properties.

    Exporting the strict boundary base would publish a spec in which ``{}`` is the
    only legal value, forbidding the feature outright.
    """
    schemas = export_openapi()["components"]["schemas"]

    assert schemas["OrderParameters"]["additionalProperties"] is True


def test_order_request_references_order_parameters_not_the_permissive_base() -> None:
    """``OrderParameters`` and ``BaseOrderParameters`` must stay distinct components.

    Once ``OrderParameters`` is open the two are structurally identical, so
    ``_dedup_identical`` keeps them apart on their descriptions alone: dropping
    either docstring silently merges them.
    """
    schemas = export_openapi()["components"]["schemas"]

    assert "BaseOrderParameters" in schemas
    assert schemas["OrderRequest"]["properties"]["order_parameters"] == {"$ref": "#/components/schemas/OrderParameters"}


def test_no_input_output_schema_variants_are_published() -> None:
    """The document must not expose pydantic's validation/serialization split.

    "Input" and "Output" appear nowhere in the STAPI vocabulary.
    """
    schemas = export_openapi()["components"]["schemas"]

    assert [name for name in schemas if name.endswith(("-Input", "-Output"))] == []
    assert {"SearchParameters", "OpportunityRequest"} <= set(schemas)


def test_merge_keeps_divergent_pairs_apart() -> None:
    """The merge must never collapse two variants that genuinely differ."""
    openapi = {
        "components": {
            "schemas": {
                "Same-Input": {"type": "object"},
                "Same-Output": {"type": "object"},
                "Differs-Input": {"type": "object", "required": ["a"]},
                "Differs-Output": {"type": "object", "required": ["b"]},
            }
        },
        "paths": {},
    }

    _merge_input_output_pairs(openapi)

    assert set(openapi["components"]["schemas"]) == {"Same", "Differs-Input", "Differs-Output"}


def test_product_scoped_operations_declare_a_missing_product() -> None:
    """Templatizing is what makes an unknown product addressable, so the templated
    paths must document a 404 the concrete routes rightly do not.
    """
    paths = export_openapi()["paths"]
    templated = {
        (path, method)
        for path, item in paths.items()
        if "{productId}" in path
        for method, operation in item.items()
        if method in _HTTP_METHODS and isinstance(operation, dict) and "404" not in operation["responses"]
    }

    assert templated == set()
