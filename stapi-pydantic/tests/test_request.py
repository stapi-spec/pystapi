from stapi_pydantic import Request


def test_create_order() -> None:
    Request.model_validate(
        {
            "datetime": "2025-03-24T00:00:00Z/..",
            "productId": "42",
            "geometry": {"type": "Point", "coordinates": [-105.1019, 40.1672]},
        }
    )


def test_create_order_with_filter() -> None:
    Request.model_validate(
        {
            "datetime": "2025-03-24T00:00:00Z/..",
            "productId": "42",
            "geometry": {"type": "Point", "coordinates": [-105.1019, 40.1672]},
            "filter": {"op": "like", "args": [{"property": "eo:instrument"}, "OLI%"]},
        }
    )
