# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `Route`, a declarative route descriptor, with `Route.to_api_route()` returning the keyword arguments for FastAPI's own `add_api_route`, and `StapiFastapiBaseRouter.register_route()` handing them over. `Route` requires a `summary`, a `tag` (the new `Tag` enum) and an `errors` set, so an operation cannot be published without a title, a heading, or an accurate statement of how it can fail.
- `Page`, exported from `stapi_fastapi`, is the one shape every list backend returns. It carries `items`, a `next_token`, an optional `number_matched`, and any collection-level `links` only the backend can know (e.g. `create-order` on a stored Opportunity Collection).
- Pagination on `GET /searches/opportunities/{searchRecordId}/statuses` and `GET /products/{productId}/opportunities/{opportunityCollectionId}`, which previously published neither `next` nor `limit` because their backends had nothing to paginate.
- `RootRouter.supports_order_statuses` and `RootRouter.supports_opportunity_search_record_statuses`, reporting whether those endpoints are registered.
- `RootRouter.opportunity_search_record_links()`, which adds a `monitor` link to a search record when the statuses endpoint is registered.
- `Product.validate_required_queryables()`, which rejects a search or order whose filter omits a predicate for a queryable the product requires.
- `PaginationTokenError`, which a backend returns inside a `Failure` when a pagination token identifies no page. The handler answers it with a 404.
- `numberMatched` is populated on every collection response the backend can count, including `GET /products`.
- `stapi_fastapi.query_params` provides the shared `Limit` and `NextToken` annotations and `DEFAULT_LIMIT`, so every paginated endpoint validates identically and publishes its bounds.
- `stapi_fastapi.path_params` provides the camelCase path parameter annotations.
- `Responses` type alias for the response-declaration mapping, and `BAD_REQUEST` / `NOT_FOUND` / `SERVER_ERROR` to compose an `errors` set from, e.g. `errors=NOT_FOUND | SERVER_ERROR`.
- Every route declares its 400 and 404 responses. 404 was raised from nine places and declared nowhere; 400 likewise.
- Operation summaries on the six routes that had none, where FastAPI was deriving titles like `Root:List-Orders` from route names.

### Changed

- **BREAKING** A request that omits a predicate for a required queryable is answered with 400 rather than 422, since it is a malformed request rather than an unprocessable one. `QueryablesError` carries the new status.
- **BREAKING** `GetOpportunitySearchRecordStatuses` and `GetOpportunityCollection` gained `next` and `limit` parameters. `GetOpportunitySearchRecordStatuses` returned `Maybe[list[OpportunitySearchStatus]]` and now returns `Maybe[Page[OpportunitySearchStatus]]`; the endpoint answers with an `OpportunitySearchStatusCollection` rather than a bare JSON array, so it can carry links and a total like every other collection. `GetOpportunityCollection` returned `Maybe[OpportunityCollection]` and now returns `Maybe[Page[Opportunity]]`; the handler assembles the collection, setting its `id` from the path and its `self`/`next` links, so a backend returns only the opportunities plus any collection-level links.
- **BREAKING** Every list backend must now return a `Page`. `GetOrders` returned `tuple[list[Order], Maybe[str], Maybe[int]]`, `SearchOpportunities` and `GetOpportunitySearchRecords` returned `tuple[list[...], Maybe[str]]`, and `GetOrderStatuses` returned `Maybe[tuple[list[...], Maybe[str]]]`. All now return `Page` (wrapped in `Maybe` where they were before): put the items in `Page.items`, the pagination token in `Page.next_token`, and the total in `Page.number_matched`.
- **BREAKING** A `limit` below 1 is rejected with a 422 instead of being silently accepted, on every paginated endpoint and in the opportunity search body. Previously the 100-item cap was applied only to `GET /products`, `limit=0` dead-ended paging, and a negative limit silently truncated the result set with no `next` link. An over-large `limit` is clamped rather than rejected: the spec makes it what the client asks for, not what the server owes, and publishes no maximum -- so neither does the document.
- **BREAKING** Path parameters are camelCase in the routes and in the exported OpenAPI document: `{orderId}`, `{searchRecordId}`, and `{opportunityCollectionId}`, joining the existing `{productId}`. Request URLs are unchanged, since path parameter names never appear in them, but generated clients that bind by parameter name need regenerating, and `url_for` calls must pass the camelCase keyword (`url_for(request, name, orderId=...)`, not `order_id=...`).
- **BREAKING** A route is declared as a `Route` and registered with `StapiFastapiBaseRouter.register_route`, which hands it to FastAPI's own `add_api_route`. `summary`, `tag` and `errors` are required, so a route cannot be registered without saying what it is called, where it is filed, or which errors it can produce. `errors` is deliberately not defaulted: a shared set merged into every route cannot be narrowed, and so published a 404 for the landing page, an endpoint that takes no input and calls no backend.
- OpenAPI tags come from the route family rather than the owning router: creating an order for a product is filed under Orders, and the opportunity routes under Opportunities, rather than all of them under Products.
- `Preference-Applied` is sent whenever the request carried a `Prefer` header, as the spec requires. It was previously sent only when the preference was `wait` and the root router supported async search, so a client that asked for a preference the server did not honour was told nothing at all.
- **BREAKING** The landing page publishes the search records link under the spec's `search-records` rel, not `opportunity-search-records`.
- A product advertises the opportunity conformance classes it is actually served under, rather than whatever it declared. An async-only product mounted on a root router without async support previously advertised classes whose routes were never registered.
- The root router advertises only the optional conformance classes whose backends were supplied, mirroring what `build_conformances` already did per product. `RootRouter(conformances=...)` now defaults to `None` rather than a fixed list.
- Conformance lists are sorted, so they no longer vary between processes.
- The `self` link of a paginated response carries the request's query parameters, so it points at the page that was returned rather than at the first page.
- **BREAKING** `ProductRouter.pagination_link` is renamed `search_pagination_link`, distinguishing the POST-bodied opportunity search `next` link from the shared query-parameter one, which now lives on the base router.
- **BREAKING** The `GET_OPPORTUNITY_SEARCH_RECORD_STATUSES` route name constant is renamed `LIST_OPPORTUNITY_SEARCH_RECORD_STATUSES`, matching its sibling list routes, and the registered route name changes with it.

### Fixed

- The opportunity search record statuses endpoint and its conformance class are gated on async opportunity search support, since the search-record endpoints they hang off only exist when async search is supported.
- `RootRouter.add_product` rejects a product whose id is already registered. `include_router` only appends, so a second product with the same id left the first router's routes serving every request -- they match first -- while `product_routers` pointed at the new one, making the two disagree about what was mounted.
- A withheld `get_order_statuses` backend is now actually withheld. The gate tested the router's own handler method instead of the backend, so it was always truthy: a server that supplied no backend still advertised the order-statuses conformance class, published `GET /orders/{orderId}/statuses`, and emitted a `monitor` link on every order, then returned a 500 when a client followed it. Every sibling gate was audited and this was the only one wrong.
- An unusable pagination token is distinguished from an incidental failure. The handlers matched a bare `Failure(ValueError())` and answered 404, so any `ValueError` a backend raised in passing -- an `int()` on unparseable input, an unrelated `list.index` miss -- was reported to the client as a page that does not exist rather than as the server error it was. Backends now return `PaginationTokenError` for a bad token; everything else stays a 500.
- A collection's `self` and `next` links carry the media type their target serves. `next` was hard-coded to `application/json`, so every geo+json collection published a next link contradicting its own response.
- A query parameter named `self` no longer fails the request. The raw query params were splatted into `URL.include_query_params` as Python keywords, colliding with that method's own `self`; repeated parameters were also collapsed to the last value.
- Operations declare only the error responses they can actually produce. A shared set was previously merged into every route and could not be narrowed, so `GET /` and `GET /conformance` published a 404 despite taking no input and calling no backend.
- `500` is declared. It is returned deliberately when a backend reports failure, so a client has to be prepared for it.
- Every operation publishes a stable `operationId`, derived from the route's prefixed name so it stays unique across a deployment mounting several products.

### Removed

- `RootRouter.order_statuses_link`. The order statuses response builds its `self` link through the shared `page_links` helper.
- A duplicate definition of the `LIST_PRODUCTS` route name constant.
- **BREAKING** The runtime dependencies the library never imported: `httpx`, `pygeofilter`, `nox`, `pydantic-settings`, and `uvicorn`. If your application imports any of these, depend on it directly. `httpx` remains a development dependency, for the test client.

## [0.8.0] - 2025-12-18

### Added

- RootRouter Callable `get_orders` now requires an additional value in the result tuple that is a count of the total number of orders
  that will be returned from pagination. When this returns `Some(int)`, the value is used for the `numberMatched` field in
  FeatureCollection returned from the /orders endpoint.  If this feature is not desired, providing a function that returns
  `Nothing` will exclude the `numberMatched` field in the response.
- ProductRouter and RootRouter now have a method `url_for` that makes the link generation code slightly cleaner and
  allows for overridding in child classes, to support proxy rewrite of the links.

### Removed

- removed dependency on `pyrfc3339` library, since only one function from it was used in tests and that function has
  been removed in newer versions of the library.

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

[0.8.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.8.0
[0.7.1]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.7.1
[0.7.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.7.0
[0.6.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.6.0
[0.5.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.5.0
[0.4.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.4.0
[0.3.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.3.0
[0.2.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.2.0
[0.1.0]: https://github.com/stapi-spec/stapi-fastapi/tree/v0.1.0
