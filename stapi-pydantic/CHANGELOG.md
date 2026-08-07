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
- `STAPI_VERSION` is now exported from the package root.

### Changed

- `STAPI_VERSION` is `0.2.0`.
- **BREAKING** `DatetimeInterval` now denotes the general interval, which may be open on one end via `..` or an empty string, and validates as a `tuple[AwareDatetime | None, AwareDatetime | None]`. The both-ends-bounded form is now `BoundedDatetimeInterval`. Code that relied on `DatetimeInterval` rejecting open ends, or on both tuple members being non-`None`, must switch to `BoundedDatetimeInterval`.
- **BREAKING** `Geometry` is the six-member STAPI union and no longer includes `GeometryCollection`. The spec enumerates exactly six geometry conformance classes, so a `GeometryCollection` was a value no implementation could declare support for. Import `geojson_pydantic.geometries.Geometry` directly if you need the wider union.

### Removed

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
