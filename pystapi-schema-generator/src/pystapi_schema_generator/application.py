"""A minimal, generic FastAPI app dedicated to OpenAPI spec export.

A STAPI application wired with a single, generically-named example product and
stub backends for every optional capability. Schema export only introspects
routes and models, so the backends simply raise ``NotImplementedError``.

The base model classes are used throughout, and nothing is imported from
``tests/``, so the exported document describes the API generically rather than
leaking fixture names.
"""

import json
import sys
from copy import deepcopy
from typing import Any, NoReturn

import yaml
from fastapi import FastAPI, status
from pydantic import ConfigDict
from stapi_fastapi.conformance import API, PRODUCT
from stapi_fastapi.models.product import Product
from stapi_fastapi.routers.base import NOT_FOUND, operation_id
from stapi_fastapi.routers.root_router import RootRouter
from stapi_pydantic import (
    STAPI_VERSION,
    OpportunityProperties,
    Provider,
    ProviderRole,
    Queryables,
)
from stapi_pydantic import (
    OrderParameters as _StrictOrderParameters,
)


# The docstring below is published verbatim as the component's `description`, so
# it is written for a spec reader.
#
# `stapi_pydantic.OrderParameters` is strict (no fields, `extra="forbid"`), which
# in a generic document would publish `additionalProperties: false` with no
# properties -- a spec in which `{}` is the only legal value. Subclassing rather
# than substituting `BaseOrderParameters` keeps the `ORP` bound satisfied and the
# component name unchanged.
class OrderParameters(_StrictOrderParameters):
    """Product-specific parameters to apply when creating an Order.

    Each Product defines its own Order Parameters JSON Schema, published at
    ``GET /products/{productId}/order-parameters``; this value must validate against
    that schema. Omitting it is equivalent to providing an empty object.
    """

    model_config = ConfigDict(extra="allow")


#: The concrete product id of the single reference product, scrubbed from the
#: published document during post-processing.
_PRODUCT_ID = "example"

#: The name the reference app's root router is mounted under; every operationId
#: begins with it.
_ROOT_ROUTER_NAME = "root"

PRODUCT_ID_PARAMETER: dict[str, Any] = {
    "name": "productId",
    "in": "path",
    "required": True,
    "schema": {"type": "string", "title": "Product Id"},
}

_HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

_SCHEMA_REF_PREFIX = "#/components/schemas/"

_SPEC_DOCS = "https://github.com/stapi-spec/stapi-spec/blob/main/docs"

#: API-level conformance classes the reference app advertises. Imported rather
#: than hardcoded so the published URIs track the STAPI version.
_ADVERTISED_CONFORMANCE: list[str] = [
    API.core,
    API.order_statuses,
    API.searches_opportunity,
    API.searches_opportunity_statuses,
]


async def _not_implemented(*args: Any, **kwargs: Any) -> NoReturn:
    """Stub backend. Never called during schema export."""
    raise NotImplementedError


def create_reference_app() -> FastAPI:
    """Build the generic reference STAPI application used for OpenAPI export."""
    provider = Provider(
        name="Example Provider",
        description="Example provider for demonstration purposes",
        roles=[ProviderRole.producer],
        url="https://example.com/provider",
    )

    example_product = Product(
        id=_PRODUCT_ID,
        title="Example Product",
        description=(
            "This is an example product that demonstrates the STAPI specification. "
            "Implementers should replace this with their actual product definitions, "
            "including specific metadata, queryable properties, and order parameters."
        ),
        license="proprietary",
        keywords=["example"],
        providers=[provider],
        links=[],
        create_order=_not_implemented,
        search_opportunities=_not_implemented,
        search_opportunities_async=_not_implemented,
        get_opportunity_collection=_not_implemented,
        queryables=Queryables,
        opportunity_properties=OpportunityProperties,
        order_parameters=OrderParameters,
        conforms_to=[PRODUCT.geojson_point, PRODUCT.opportunities, PRODUCT.opportunities_async],
    )

    root_router = RootRouter(
        get_orders=_not_implemented,
        get_order=_not_implemented,
        get_order_statuses=_not_implemented,
        get_opportunity_search_records=_not_implemented,
        get_opportunity_search_record=_not_implemented,
        get_opportunity_search_record_statuses=_not_implemented,
        conformances=list(_ADVERTISED_CONFORMANCE),
        name=_ROOT_ROUTER_NAME,
    )
    root_router.add_product(example_product)

    app: FastAPI = FastAPI(
        title="STAPI",
        description=(
            "The Sensor Tasking API (STAPI) defines a JSON-based web API to query for "
            "spatio-temporal analytic and data products derived from remote sensing "
            "(satellite or airborne) providers. The specification supports both products "
            "derived from new tasking and products from provider archives."
        ),
        version=STAPI_VERSION,
        contact={
            "name": "STAPI Specification Organization",
            "url": "https://github.com/stapi-spec",
        },
        openapi_tags=[
            {
                "name": "Root",
                "description": "The landing page, communicating API metadata, conformance, and links.",
                "externalDocs": {
                    "description": "STAPI Core Specification",
                    "url": f"{_SPEC_DOCS}/conformances/core/README.md",
                },
            },
            {
                "name": "Conformance",
                "description": "Conformance classes implemented by this API.",
                "externalDocs": {
                    "description": "STAPI Conformance Classes",
                    "url": f"{_SPEC_DOCS}/conformances/README.md",
                },
            },
            {
                "name": "Products",
                "description": "Endpoints for discovering and describing remote sensing data products.",
                "externalDocs": {
                    "description": "STAPI Product Specification",
                    "url": f"{_SPEC_DOCS}/spec/product/README.md",
                },
            },
            {
                "name": "Orders",
                "description": "Endpoints for creating and monitoring remote sensing data orders.",
                "externalDocs": {
                    "description": "STAPI Order Specification",
                    "url": f"{_SPEC_DOCS}/spec/order/README.md",
                },
            },
            {
                "name": "Opportunities",
                "description": "Endpoints for searching remote sensing acquisition opportunities.",
                "externalDocs": {
                    "description": "STAPI Opportunity Specification",
                    "url": f"{_SPEC_DOCS}/spec/opportunity/README.md",
                },
            },
        ],
    )
    app.include_router(root_router, prefix="")

    _original_openapi = app.openapi

    def _openapi_with_external_docs() -> dict[str, Any]:
        schema = _original_openapi()
        schema["externalDocs"] = {
            "description": "STAPI Specification Documentation",
            "url": "https://stapi-spec.github.io/stapi-spec/",
        }
        return schema

    app.openapi = _openapi_with_external_docs  # type: ignore[method-assign]

    return app


def _operations(openapi: dict[str, Any]) -> list[dict[str, Any]]:
    """Every operation object in the document."""
    return [
        operation
        for path_item in openapi["paths"].values()
        for method, operation in path_item.items()
        if method in _HTTP_METHODS and isinstance(operation, dict)
    ]


def _genericize_operation_ids(openapi: dict[str, Any]) -> None:
    """Strip this app's own names out of the published operationIds.

    ``root_example_create_order`` becomes ``create_order``, the way
    :func:`_templatize_product_paths` makes the paths lose them. Dropping the
    product segment can make a product-scoped id collide with a root-level one;
    those keep a ``product_`` prefix (``product_conformance``).
    """
    root_prefix = operation_id(f"{_ROOT_ROUTER_NAME}:")
    product_prefix = operation_id(f"{_ROOT_ROUTER_NAME}:{_PRODUCT_ID}:")

    def strip(published: str) -> tuple[str, bool]:
        if published.startswith(product_prefix):
            return published[len(product_prefix) :], True
        if published.startswith(root_prefix):
            return published[len(root_prefix) :], False
        return published, False

    operations = _operations(openapi)
    stripped = [strip(operation["operationId"]) for operation in operations]
    root_level = {base for base, product_scoped in stripped if not product_scoped}

    for operation, (base, product_scoped) in zip(operations, stripped):
        operation["operationId"] = f"product_{base}" if product_scoped and base in root_level else base


def _base_schema_name(name: str, schema: dict[str, Any]) -> str:
    """Return a clean base name for a (possibly generic) schema.

    Pydantic names generic-model schemas after their parameterization
    (``Order_OrderStatus_``), but the ``title`` carries the readable form
    (``Order[OrderStatus]``), so the clean base is the identifier before the
    first ``[``. FastAPI's ``-Input`` / ``-Output`` suffixes are preserved.
    """
    for suffix in ("-Input", "-Output"):
        if name.endswith(suffix):
            return _base_schema_name(name[: -len(suffix)], schema) + suffix
    title: str = schema.get("title", "") or ""
    if "[" in title:
        return title.split("[", 1)[0]
    return name


def _schema_name(ref: Any) -> str | None:
    """Resolve a local component reference to its schema name.

    Accepts both spellings a reference can take in the document: a full
    ``#/components/schemas/<name>`` pointer, and the bare ``<name>`` that OpenAPI
    also permits for ``discriminator.mapping`` values.
    """
    if not isinstance(ref, str):
        return None
    if ref.startswith(_SCHEMA_REF_PREFIX):
        return ref[len(_SCHEMA_REF_PREFIX) :]
    return ref if "/" not in ref and "#" not in ref else None


def _local_ref_slots(node: dict[str, Any]) -> list[tuple[dict[str, Any], Any]]:
    """Return the ``(container, key)`` slots in ``node`` that hold a local reference.

    A node references components in two places: its own ``$ref``, and the values
    of a ``discriminator.mapping``. The latter are bare strings, so a traversal
    that only looks for ``$ref`` silently misses them -- and the exported document
    carries such a mapping on every ``geometry`` field.
    """
    slots: list[tuple[dict[str, Any], Any]] = [(node, "$ref")] if "$ref" in node else []
    discriminator = node.get("discriminator")
    mapping = discriminator.get("mapping") if isinstance(discriminator, dict) else None
    if isinstance(mapping, dict):
        slots.extend((mapping, key) for key in mapping)
    return slots


def _rewrite_refs(node: Any, rename: dict[str, str]) -> Any:
    """Recursively rewrite local reference schema names according to ``rename``."""
    if isinstance(node, dict):
        for container, key in _local_ref_slots(node):
            name = _schema_name(container[key])
            if name is not None and name in rename:
                container[key] = _SCHEMA_REF_PREFIX + rename[name]
        for value in node.values():
            _rewrite_refs(value, rename)
    elif isinstance(node, list):
        for item in node:
            _rewrite_refs(item, rename)
    return node


def _canonical(schema: dict[str, Any]) -> str:
    """Deterministic, title-insensitive signature for deduplication."""
    without_title = {k: v for k, v in schema.items() if k != "title"}
    return json.dumps(without_title, sort_keys=True)


def _assign_clean_names(schemas: dict[str, Any]) -> dict[str, str]:
    """Map each current schema name to its clean, unique target name.

    Schemas that collapse to the same base name are disambiguated: FastAPI's
    ``-Input`` / ``-Output`` validation/serialization pairs keep that suffix;
    any other genuine collision gets a stable numeric suffix ordered by the
    schema's canonical (title-insensitive) signature.
    """
    groups: dict[str, list[str]] = {}
    for name, schema in schemas.items():
        groups.setdefault(_base_schema_name(name, schema), []).append(name)

    rename: dict[str, str] = {}
    for base, members in groups.items():
        if len(members) == 1:
            rename[members[0]] = base
            continue
        io_members = [m for m in members if m in (base + "-Input", base + "-Output")]
        if len(io_members) == len(members):
            for m in io_members:
                rename[m] = m  # already a clean, distinct Input/Output name
            continue
        for index, m in enumerate(sorted(members, key=lambda m: (_canonical(schemas[m]), m))):
            rename[m] = base if index == 0 else f"{base}-{index + 1}"
    return rename


def _dedup_identical(schemas: dict[str, Any]) -> dict[str, str]:
    """Return a ``duplicate -> survivor`` map for title-insensitive duplicates.

    Names carrying a mode suffix sort last, so that a duplicate pair never elects
    ``X-Input`` as the survivor and publishes the suffix as if it meant something.
    """
    signatures: dict[str, str] = {}
    dedup: dict[str, str] = {}
    for name in sorted(schemas, key=lambda n: (n.endswith(("-Input", "-Output")), n)):
        signature = _canonical(schemas[name])
        if signature in signatures:
            dedup[name] = signatures[signature]
        else:
            signatures[signature] = name
    return dedup


def _clean_schema_names(openapi: dict[str, Any]) -> None:
    """Give component schemas readable, generic, deterministic names.

    Collapses Pydantic generic-parameter mangling to the base model name,
    deduplicates structurally identical schemas, and rewrites every ``$ref``
    consistently. Iterates to a fixpoint because collapsing one model can make
    its containers identical too.
    """
    schemas: dict[str, Any] = openapi["components"]["schemas"]
    paths = openapi["paths"]

    while True:
        rename = _assign_clean_names(schemas)
        renamed: dict[str, Any] = {}
        for old, schema in schemas.items():
            schema = {**schema, "title": rename[old]}
            renamed[rename[old]] = schema
        _rewrite_refs(renamed, rename)
        _rewrite_refs(paths, rename)
        schemas = renamed

        dedup = _dedup_identical(schemas)
        for name in dedup:
            del schemas[name]
        _rewrite_refs(schemas, dedup)
        _rewrite_refs(paths, dedup)

        if not any(old != new for old, new in rename.items()) and not dedup:
            break

    openapi["components"]["schemas"] = dict(sorted(schemas.items()))


def _merge_input_output_pairs(openapi: dict[str, Any]) -> None:
    """Collapse ``X-Input``/``X-Output`` pairs that describe the same thing.

    FastAPI asks pydantic for both a validation and a serialization schema when a
    model appears in a request and a response. Pydantic re-merges them unless that
    would be ambiguous, which it always looks for a self-recursive model, so the
    split cascades to everything containing a geometry.

    Merging here rather than disabling FastAPI's ``separate_input_output_schemas``,
    which would generate the whole document in validation mode and so drop every
    serialization alias and serialization-required field.

    The candidate set starts optimistic and shrinks: a pair survives only if the
    two members are identical *once the merge is applied*.
    """
    schemas: dict[str, Any] = openapi["components"]["schemas"]
    bases = {
        name[: -len("-Input")]
        for name in schemas
        if name.endswith("-Input") and f"{name[: -len('-Input')]}-Output" in schemas
    }

    while bases:
        rename = {f"{base}{suffix}": base for base in bases for suffix in ("-Input", "-Output")}
        divergent = {
            base
            for base in bases
            if _canonical(_rewrite_refs(deepcopy(schemas[f"{base}-Input"]), rename))
            != _canonical(_rewrite_refs(deepcopy(schemas[f"{base}-Output"]), rename))
        }
        if not divergent:
            break
        bases -= divergent

    if not bases:
        return

    rename = {f"{base}{suffix}": base for base in bases for suffix in ("-Input", "-Output")}
    for base in bases:
        schemas[base] = {**schemas.pop(f"{base}-Output"), "title": base}
        del schemas[f"{base}-Input"]
    _rewrite_refs(schemas, rename)
    _rewrite_refs(openapi["paths"], rename)
    openapi["components"]["schemas"] = dict(sorted(schemas.items()))


def _templatize_product_paths(openapi: dict[str, Any]) -> dict[str, Any]:
    """Rewrite the concrete product paths into templated form.

    ``/products/{id}`` -> ``/products/{productId}`` and
    ``/products/{id}/...`` -> ``/products/{productId}/...``, injecting a
    ``productId`` path parameter into each operation.
    """
    concrete = f"/products/{_PRODUCT_ID}"
    paths: dict[str, Any] = openapi["paths"]
    new_paths: dict[str, Any] = {}

    for path, path_item in paths.items():
        if path == concrete:
            new_path = "/products/{productId}"
        elif path.startswith(concrete + "/"):
            new_path = "/products/{productId}/" + path[len(concrete + "/") :]
        else:
            new_paths[path] = path_item
            continue

        path_item = deepcopy(path_item)
        for method, operation in path_item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            parameters = operation.setdefault("parameters", [])
            parameters.insert(0, deepcopy(PRODUCT_ID_PARAMETER))
            # the reference app's one concrete product declares no 404, but the
            # templated form can be asked for a product that does not exist
            operation.setdefault("responses", {}).setdefault(
                str(status.HTTP_404_NOT_FOUND),
                deepcopy(NOT_FOUND[status.HTTP_404_NOT_FOUND]),
            )
        if new_path in new_paths:
            raise AssertionError(
                f"{new_path} was produced twice: the reference app must register exactly one "
                "product, otherwise templatizing collapses several products onto one path and "
                "silently publishes only the last."
            )
        new_paths[new_path] = path_item

    openapi["paths"] = new_paths
    return openapi


def export_openapi() -> dict[str, Any]:
    """Build the reference app and return its post-processed OpenAPI schema."""
    # The passes below mutate in place, and ``app.openapi()`` returns FastAPI's
    # cached document, so copy first: without this a second call would
    # post-process an already-post-processed document.
    openapi = deepcopy(create_reference_app().openapi())

    _merge_input_output_pairs(openapi)
    _clean_schema_names(openapi)
    _genericize_operation_ids(openapi)
    _templatize_product_paths(openapi)
    return openapi


def main() -> None:
    """Write the exported OpenAPI document as YAML to stdout."""
    sys.stdout.write(yaml.safe_dump(export_openapi(), sort_keys=True))


if __name__ == "__main__":
    main()
