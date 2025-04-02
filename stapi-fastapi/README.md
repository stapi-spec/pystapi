# STAPI FastAPI - Sensor Tasking API with FastAPI

> [!WARNING]
> The whole [STAPI spec] is very much a work in progress, so things are guaranteed to be not correct.

## Usage

STAPI FastAPI provides an `fastapi.APIRouter` which must be included in
`fastapi.FastAPI` instance.

### Pagination

4 endpoints currently offer pagination:

- `GET`: `'/orders`, `/products`, `/orders/{order_id}/statuses`
- `POST`: `/opportunities`.

Pagination is token based and follows recommendations in the [STAC API pagination].
Limit and token are passed in as query params for `GET` endpoints, and via the body as
separate key/value pairs for `POST` requests.

If pagination is available and more records remain the response object will contain a
`next` link object that can be used to get the next page of results. No `next` `Link`
returned indicates there are no further records available.

`limit` defaults to 10 and maxes at 100.

## ADRs

ADRs can be found in in the [adrs](./adrs/README.md) directory.

### Implementing a backend

- The test suite assumes the backend can be instantiated without any parameters
  required by the constructor.

[STAPI spec]: https://github.com/stapi-spec/stapi-spec
[STAC API pagination]: https://github.com/radiantearth/stac-api-spec/blob/release/v1.0.0/item-search/examples.md#paging-examples
