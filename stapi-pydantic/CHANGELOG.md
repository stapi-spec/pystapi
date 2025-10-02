<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `OrderPayload` changed so that the `geometry` and `datetime` fields are optional. This is in support of ordering non-tasked imagery (i.e. already collected imagery) where `geometry` and `datetime` are not necessary to fulfill the order.

### Added

- ProductRouter and RootRouter now have a method `url_for` that makes the link generation code slightly cleaner and
  allows for overridding in child classes, to support proxy rewrite of the links.

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
[0.0.4]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.3...stapi-pydantic%2Fv0.0.4
[0.0.3]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.2...stapi-pydantic%2Fv0.0.3
[0.0.2]: https://github.com/stapi-spec/pystapi/compare/stac-pydantic/stapi-pydantic%2Fv0.0.1...stapi-pydantic%2Fv0.0.2
[0.0.1]: https://github.com/stapi-spec/pystapi/releases/tag/stapi-pydantic%2Fv0.0.1
