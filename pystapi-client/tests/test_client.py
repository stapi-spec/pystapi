from pystapi_client.client import Client
from pystapi_client.conformance import ConformanceClasses
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


def test_async_opportunities_uri_matches_reference_server() -> None:
    server_advertised = "https://stapi.example.com/v0.2.0/opportunities-async"
    assert ConformanceClasses.ASYNC_OPPORTUNITIES.pattern.match(server_advertised)


def test_sync_opportunities_uri_does_not_match_async_uri() -> None:
    async_uri = "https://stapi.example.com/v0.2.0/opportunities-async"
    assert not ConformanceClasses.OPPORTUNITIES.pattern.match(async_uri)
    assert ConformanceClasses.OPPORTUNITIES.pattern.match("https://stapi.example.com/v0.2.0/opportunities")


# --- Item 1: version pattern is a single path segment, anchored with \Z ---


def test_version_pattern_matches_single_version_segment() -> None:
    pattern = ConformanceClasses.OPPORTUNITIES.pattern
    assert pattern.match("https://stapi.example.com/v0.2.0/opportunities")


def test_version_pattern_rejects_extra_path_segments() -> None:
    pattern = ConformanceClasses.OPPORTUNITIES.pattern
    assert not pattern.match("https://stapi.example.com/v0.2.0/foo/opportunities")


def test_version_pattern_rejects_empty_version() -> None:
    pattern = ConformanceClasses.OPPORTUNITIES.pattern
    assert not pattern.match("https://stapi.example.com/v/opportunities")


def test_version_pattern_rejects_trailing_newline() -> None:
    pattern = ConformanceClasses.OPPORTUNITIES.pattern
    assert not pattern.match("https://stapi.example.com/v0.2.0/opportunities\n")


# --- Item 2: API-level extension conformance classes exist in the enum ---


def test_api_level_extension_classes_exist_and_match() -> None:
    order_statuses = ConformanceClasses.get_by_name("ORDER_STATUSES")
    searches_opportunity = ConformanceClasses.get_by_name("SEARCHES_OPPORTUNITY")
    searches_opportunity_statuses = ConformanceClasses.get_by_name("SEARCHES_OPPORTUNITY_STATUSES")

    assert order_statuses.pattern.match("https://stapi.example.com/v0.2.0/order-statuses")
    assert searches_opportunity.pattern.match("https://stapi.example.com/v0.2.0/searches-opportunity")
    assert searches_opportunity_statuses.pattern.match("https://stapi.example.com/v0.2.0/searches-opportunity-statuses")


def test_searches_opportunity_does_not_match_statuses_uri() -> None:
    searches_opportunity = ConformanceClasses.get_by_name("SEARCHES_OPPORTUNITY")
    assert not searches_opportunity.pattern.match("https://stapi.example.com/v0.2.0/searches-opportunity-statuses")


# --- Item 3 / 4: product-scoped opportunity capability checks ---


def test_supports_opportunities_reads_product_conformance(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")
    assert client.product_supports_opportunities("multispectral") is True


def test_supports_async_opportunities_reads_product_conformance(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")
    assert client.product_supports_async_opportunities("multispectral") is True


def test_product_without_opportunities_returns_false(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")
    assert client.product_supports_opportunities("spotlight") is False
    assert client.product_supports_async_opportunities("spotlight") is False


def test_opportunity_support_does_not_depend_on_root_conformance(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")
    # Root conformsTo must not advertise the product-level opportunity classes.
    assert not client.has_conformance(ConformanceClasses.OPPORTUNITIES)
    assert not client.has_conformance(ConformanceClasses.ASYNC_OPPORTUNITIES)
    # Yet the product does support opportunities per its own conformsTo.
    assert client.product_supports_opportunities("multispectral") is True


def test_root_advertises_api_level_extension_classes(api: MockRouter) -> None:
    client = Client.open(url="http://stapi.test")
    assert client.has_conformance(ConformanceClasses.CORE)
    assert client.has_conformance("ORDER_STATUSES")
    assert client.has_conformance("SEARCHES_OPPORTUNITY")
