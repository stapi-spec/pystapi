<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `JsonSchema`, a root model holding a JSON Schema document, with `JsonSchema.from_model` deriving one from a pydantic model class.
- `Queryables.required_property_names`, the required set read from the published queryables JSON Schema and cached per subclass.
- `Geometry`, the union of the six geometry types STAPI defines, discriminated on `type`. Exported from the package root.
- A `stapi_pydantic.geometry` module providing `compute_geometry_bbox`, `bbox_from_geometry_input`, and `union_bboxes`.
- `BoundedDatetimeInterval`, for intervals that are bounded at both ends.
- `cql2_property_names`, which collects the property names referenced by a CQL2 JSON filter.
- `SearchParameters`, the Search Parameters Object (`datetime`, `geometry`, `filter`) shared by the Opportunity Request and the Order Request. It permits extra fields, so provider extension parameters round-trip instead of being dropped.
- `ProductCollection`, the new name for `ProductsCollection` (see Changed).
- `OpportunitySearchStatusCollection`, the collection wrapper for the statuses of an Opportunity Search Record.
- `stapi_type` and `stapi_version` on `Opportunity`, `OpportunityCollection`, `OpportunitySearchRecord`, `OpportunitySearchRecordCollection`, `OrderCollection`, and `OrderStatusCollection`.
- `BaseOrderParameters`, a permissive base for order parameters at rest, and `StoredOrderRequest`, the form an Order Request takes once it is persisted inside `OrderProperties`. `OrderParameters` is now a strict (`extra="forbid"`) subclass of `BaseOrderParameters`.
- `OrderStatus` and `OpportunitySearchStatus` are generic over their status code set, so an implementation can constrain it with its own `StrEnum`, e.g. `OrderStatus[MyCodes]`.
- `STAPI_VERSION` is now exported from the package root.

### Changed

- `STAPI_VERSION` is `0.2.0`.
- **BREAKING** `DatetimeInterval` now denotes the general interval, which may be open on one end via `..` or an empty string, and validates as a `tuple[AwareDatetime | None, AwareDatetime | None]`. The both-ends-bounded form is now `BoundedDatetimeInterval`. Code that relied on `DatetimeInterval` rejecting open ends, or on both tuple members being non-`None`, must switch to `BoundedDatetimeInterval`.
- **BREAKING** `Geometry` is the six-member STAPI union and no longer includes `GeometryCollection`. The spec enumerates exactly six geometry conformance classes, so a `GeometryCollection` was a value no implementation could declare support for. Import `geojson_pydantic.geometries.Geometry` directly if you need the wider union.
- `CQL2Filter` is typed as `dict[str, Any]` rather than a bare `dict`.
- **BREAKING** `Link` omits its unset fields from `model_dump()` as well as from JSON output. The `None`-filtering serializer it previously carried applied only to JSON dumps.
- **BREAKING** Models that declare aliases now serialize by alias. `model_dump()` emits `conformsTo` on `Conformance` and `type` on `Product`, where it previously emitted the Python field names `conforms_to` and `type_`. Callers already passing `by_alias=True` are unaffected; callers reading the Python names out of a dump must switch to the wire names.
- **BREAKING** `Product.conformsTo` and `RootResponse.conformsTo` are spelled `conforms_to` in Python, matching `Conformance`. The wire name is unchanged: all three validate from either `conformsTo` or `conforms_to` and serialize as `conformsTo`. Keyword construction and attribute access must use the new name.
- **BREAKING** `Provider.roles` and `Provider.url` are optional. Both were required, which made a provider that publishes neither unrepresentable; they are now omitted from output rather than published empty or null.
- **BREAKING** `OrderStatuses` is renamed `OrderStatusCollection`, matching its sibling collections, and gains `stapi_type` and `stapi_version`.
- **BREAKING** `bbox` is required and non-nullable on `Order` and `Opportunity`, and is derived from the geometry when the caller omits it. `Order` previously excluded `bbox` from its output when unset. Collection `bbox` stays optional and is unioned from the members, and is omitted rather than emitted as null when there are none.
- `Order` and `OrderCollection` derive from `geojson_pydantic`'s `Feature` and `FeatureCollection` again, rather than re-implementing them on top of `_GeoJsonBase`. Field order in a dump follows the base classes, so `id` now trails `geometry` and `properties`.
- **BREAKING** `OrderCollection` offers the same iteration surface as `OpportunityCollection`: `collection.iter()` and `collection.length`, in place of `iter(collection)`, `len(collection)`, and `collection[i]`. Its `__iter__` override shadowed the one pydantic reserves, which broke `dict(collection)`.
- **BREAKING** `Opportunity.geometry` and `Opportunity.properties` are required and non-nullable, and `Opportunity.id` is string-only. `Feature` typed geometry and properties as nullable, so `model_validate({"geometry": None, ...})` was accepted and produced a dump that violated the spec.
- **BREAKING** `status_code` on `OrderStatus` and `OpportunitySearchStatus` accepts any string by default, since the spec lets providers add statuses through extensions. Known codes still validate to the enum. Code that assumed an `OrderStatusCode` instance must handle a plain `str`, or parameterize the model with its own code set.
- Optional status fields (`reason_code`, `reason_text`) are omitted rather than serialized as null, and so are correspondingly not marked required.
- `typing-extensions >= 4.12` is now required, for `TypeVar` defaults.
- Spec-REQUIRED fields that carry defaults (`type`, `stapi_type`, `stapi_version`, `links`, `conformsTo`, and so on) are now marked required in the serialization JSON Schema, since they are always present in a response.
- **BREAKING** `ProductsCollection` is renamed to `ProductCollection`, matching its own `stapi_type` and the spec. The old name is gone rather than aliased; update imports. The model also replaces its aliased `type` field with `stapi_type`, so responses carry `"stapi_type": "ProductCollection"` rather than `"type": "ProductCollection"`, and gains `stapi_version`.
- **BREAKING** `Product.description` is required, per the spec. It previously defaulted to the empty string.
- **BREAKING** `OpportunityRequest` (was `OpportunityPayload`) and `OrderRequest` (was `OrderPayload`) now compose `SearchParameters` instead of declaring `datetime`, `geometry`, and `filter` themselves. A request body that was `{"datetime": ..., "geometry": ..., "filter": ...}` becomes `{"search_parameters": {"datetime": ..., "geometry": ..., "filter": ...}}`.
- **BREAKING** `OrderRequest.order_parameters` is optional and defaults to an empty object. It was previously required. Products whose `OrderParameters` model has required fields still make it effectively required, via validation.
- **BREAKING** `OrderProperties` carries a single `order_request` (a `StoredOrderRequest`) in place of the former `search_parameters`, `opportunity_properties`, and `order_parameters` fields.
- **BREAKING** `OpportunitySearchRecord.opportunity_request` is replaced by `search_parameters`, a `SearchParameters` rather than a whole request object. A record describes what was searched for, not the request body that carried it; holding the request meant every record echoed back whatever `limit`/`next` the client happened to page with, so two records describing an identical search differed if the clients paged differently. `OpportunitySearchRecordCollection` (was `OpportunitySearchRecords`) holds its items in `records` rather than `search_records`.
- **BREAKING** `OpportunityRequest.limit` is `int | None` with a lower bound of 1, and defaults to `None`. It defaulted to 10, which asserted a page size the client never asked for; the default is the server's to choose.

### Fixed

- Collection `bbox` computation no longer recurses without bound on a collection with no features.
- Computing a bbox for a geometry with no coordinates raises a clear error.
- `OrderStatus.new` respects the class it is called on. It constructed a bare `OrderStatus` regardless, so a parameterized `OrderStatus[MyCodes]` returned the wrong type and accepted codes outside its enum.
- `OrderStatusCollection` no longer emits a second, unconstrained `OrderStatus-2` schema whose `status_code` had no schema at all.
- Stored order requests and search parameters round-trip unknown fields rather than dropping them.
- A malformed CQL2 filter is reported as a validation error. `cql2` raises its own exception types, which pydantic does not convert, so an invalid filter escaped validation and surfaced as a server error rather than a rejected request.

### Removed

- **BREAKING** The pre-0.2.0 compatibility aliases `ProductsCollection`, `OrderPayload`, `OpportunityPayload`, `OrderSearchParameters`, `OpportunitySearchRecords` and `OrderStatuses` are gone. Use `ProductCollection`, `OrderRequest`, `OpportunityRequest`, `SearchParameters`, `OpportunitySearchRecordCollection` and `OrderStatusCollection`.
- The unused `Props`, `Geom`, and `OPP` type variables in `stapi_pydantic.order`.
- **BREAKING** `JsonSchemaModel` is gone. It annotated a `type[BaseModel]` with a `PlainValidator`/`PlainSerializer` pair so a model class could stand in for its own schema, which meant the published document carried an orphan `BaseModel` component and the value could not be read back. Build a `JsonSchema` with `JsonSchema.from_model(YourModel)` instead.

## [0.1.0] - 2025-12-18

### Changed

- pydantic >= 2.12 is now required.

## [0.0.4] - 2025-07-17

### Added

- `OrderStatus.new` ([#116](https://github.com/stapi-spec/pystapi/pull/116))

### Fixed

- json-schema for `datetime` ([#114](https://github.com/stapi-spec/pystapi/pull/114))

## [0.0.3] - 2025-04-24

### Added

- python `3.11` support ([#73](https://github.com/stapi-spec/pystapi/pull/73))
- `stapi_type` and `stapi_version` ([#54](https://github.com/stapi-spec/pystapi/pull/54))

### Changed

- `s/constraints/queryables/` ([#74](https://github.com/stapi-spec/pystapi/pull/74))
- `s/canceled/cancelled/` ([#75](https://github.com/stapi-spec/pystapi/pull/75))

## [0.0.2] - 2025-04-02

### Changed

- Added more top-level imports, removed conformance urls ([#51](https://github.com/stapi-spec/pystapi/pull/51))

## [0.0.1] - 2025-04-01

Initial release.

[unreleased]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.4...main
[0.1.0]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.4...stapi-pydantic%2Fv0.1.0
[0.0.4]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.3...stapi-pydantic%2Fv0.0.4
[0.0.3]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.2...stapi-pydantic%2Fv0.0.3
[0.0.2]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.1...stapi-pydantic%2Fv0.0.2
[0.0.1]: https://github.com/stapi-spec/pystapi/releases/tag/stapi-pydantic%2Fv0.0.1
