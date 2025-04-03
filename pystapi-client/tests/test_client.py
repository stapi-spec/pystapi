import respx
from pystapi_client.client import Client
from stapi_pydantic import Link


def test_get_products(mocked_api: respx.MockRouter) -> None:
    client = Client.open(url="https://stapi.example.com")

    products = list(client.get_products())
    assert len(products) == 2


def test_get_products_paginated(mocked_api: respx.MockRouter) -> None:
    client = Client.open(url="https://stapi.example.com")

    products = list(client.get_products(limit=1))
    assert len(products) == 2


def test_pagination(mocked_api: respx.MockRouter) -> None:
    client = Client.open(url="https://stapi.example.com")

    products_link = Link(href="https://stapi.example.com/products", method="GET", body={"limit": 1}, rel="")
    for products_collection in client.stapi_io.get_pages(products_link, "products"):
        assert len(products_collection["products"]) == 1
