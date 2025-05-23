# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2025-04-25

### Fixed

- Add stapi-pydantic as a dependency

## [0.7.0] - 2025-04-18

### Fixed

- Add parameter method as "POST" to create-order link

## Added

- Add constants for route names to be used in link href generation
- Opportunity search statuses ([#78](https://github.com/stapi-spec/pystapi/pull/78))
- Conformance url to product ([#85](https://github.com/stapi-spec/pystapi/pull/85))

## Changed

- Renamed all exceptions to errors ([#41](https://github.com/stapi-spec/pystapi/pull/41))
- stapi-fastapi is now using stapi-pydantic models, deduplicating code
- Product in stapi-fastapi is now subclass of Product from stapi-pydantic
- How conformances work ([#90](https://github.com/stapi-spec/pystapi/pull/90))
- Async behaviors align with spec changes ([#90](https://github.com/stapi-spec/pystapi/pull/90))

## [0.6.0] - 2025-02-11

### Added

- Added token-based pagination to `GET /orders`, `GET /products`,
  `GET /orders/{order_id}/statuses`, and `POST /products/{product_id}/opportunities`.
- Optional and Extension STAPI Status Codes "scheduled", "held", "processing", "reserved", "tasked",
  and "user_canceled"
- Asynchronous opportunity search. If the root router supports asynchronous opportunity
  search, all products must support it. If asynchronous opportunity search is
  supported, `POST` requests to the `/products/{productId}/opportunities` endpoint will
  default to asynchronous opportunity search unless synchronous search is also supported
  by the `product` and a `Prefer` header in the `POST` request is set to `wait`.
- Added the `/products/{productId}/opportunities/` and `/searches/opportunities`
  endpoints to support asynchronous opportunity search.

### Changed

- Replaced the root and product backend Protocol classes with Callable type aliases to
  enable future changes to make product opportunity searching, product ordering, and/or
  asynchronous (stateful) product opportunity searching optional.
- Backend methods that support pagination now return tuples to include the pagination
  token.
- Moved `OrderCollection` construction from the root backend to the `RootRouter`
  `get_orders` method.
- Renamed `OpportunityRequest` to `OpportunityPayload` so that would not be confused as
  being a subclass of the Starlette/FastAPI Request class.

### Fixed

- Opportunities Search result now has the search body in the `create-order` link.

## [0.5.0] - 2025-01-08

### Added

- Endpoint `/orders/{order_id}/statuses` supporting `GET` for retrieving statuses. The entity returned by this conforms
  to the change proposed in [stapi-spec#239](https://github.com/stapi-spec/stapi-spec/pull/239).
- RootBackend has new method `get_order_statuses`
- `*args`/`**kwargs` support in RootRouter's `add_product` allows to configure underlyinging ProductRouter

### Changed

- OrderRequest renamed to OrderPayload

### Removed

- Endpoint `/orders/{order_id}/statuses` supporting `POST` for updating current status was added and then
  removed prior to release
- RootBackend method `set_order_status` was added and then removed

### Fixed

- Exception logging

## [0.4.0] - 2024-12-11

### Changed

- The concepts of Opportunity search Constraint and Opportunity search result Opportunity Properties are now separate,
  recognizing that they have related attributes, but not neither the same attributes or the same values for those attributes.

## [0.3.0] - 2024-12-6

### Changed

- OrderStatusCode and ProviderRole are now StrEnum instead of (str, Enum)
- All types using `Result[A, Exception]` have been replace with the equivalent type `ResultE[A]`
- Order and OrderCollection extend \_GeoJsonBase instead of Feature and FeatureCollection, to allow for tighter
  constraints on fields

## [0.2.0] - 2024-11-23

### Changed

- RootBackend and ProductBackend protocols use `returns` library types Result and Maybe instead of
  raising exceptions.
- Create Order endpoint from `.../order` to `.../orders`
- Order field `id` must be a string, instead of previously allowing int. This is because while an
  order ID may an integral numeric value, it is not a "number" in the sense that math will be performed
  order ID values, so string represents this better.

## [0.1.0] - 2024-11-15

Initial release

### Added

- Conformance endpoint `/conformance` and root body `conformsTo` attribute.
- Field `product_id` to Opportunity and Order Properties
- Endpoint /product/{productId}/order-parameters.
- Links in Product entity to order-parameters and constraints endpoints for
  that product.
- Add links `opportunities` and `create-order` to Product
- Add link `create-order` to OpportunityCollection

[0.7.1]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.7.1
[0.7.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.7.0
[0.6.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.6.0
[0.5.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.5.0
[0.4.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.4.0
[0.3.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.3.0
[0.2.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.2.0
[0.1.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.1.0
