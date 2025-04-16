from pystapi_client.client import Client
from respx import MockRouter
from stapi_pydantic import Link


def test_get_products(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")

    products = list(client.get_products())
    assert len(products) == 2


def test_get_products_paginated(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")

    products = list(client.get_products(limit=1))
    assert len(products) == 2


def test_pagination(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")

    products_link = Link(href="http://stapi.test/products", method="GET", body={"limit": 1}, rel="")
    for products_collection in client.stapi_io.get_pages(products_link, "products"):
        assert len(products_collection["products"]) == 1
