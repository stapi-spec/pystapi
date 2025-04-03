import re
import urllib
import urllib.parse
import warnings
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime
from typing import Any

from httpx import URL, Request
from httpx._types import TimeoutTypes
from pydantic import AnyUrl
from stapi_pydantic import (
    CQL2Filter,
    Link,
    Opportunity,
    OpportunityCollection,
    OpportunityPayload,
    Order,
    OrderCollection,
    OrderPayload,
    Product,
    ProductsCollection,
)

from pystapi_client.conformance import ConformanceClasses
from pystapi_client.exceptions import APIError
from pystapi_client.stapi_api_io import StapiIO
from pystapi_client.warnings import NoConformsTo

DEFAULT_LINKS = [
    {
        "endpoint": "/conformance",
        "rel": "conformance",
        "method": "GET",
    },
    {
        "endpoint": "/products",
        "rel": "products",
        "method": "GET",
    },
]


class Client:
    """A Client for interacting with the root of a STAPI

    Instances of the ``Client`` class provide a convenient way of interacting
    with STAPI APIs that conform to the [STAPI API spec](https://github.com/stapi-spec/stapi-spec).
    """

    stapi_io: StapiIO
    conforms_to: list[str]
    links: list[Link]

    def __init__(self, stapi_io: StapiIO) -> None:
        self.stapi_io = stapi_io

    def __repr__(self) -> str:
        return f"<Client {self.stapi_io.root_url}>"

    @classmethod
    def open(
        cls,
        url: str,
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
        request_modifier: Callable[[Request], Request] | None = None,
        timeout: TimeoutTypes | None = None,
    ) -> "Client":
        """Opens a STAPI API client.

        Args:
            url: The URL of a STAPI API
            headers: Optional dictionary of additional headers to use in all requests
                made to any part of this STAPI API
            parameters: Optional dictionary of query string parameters to
                include in all requests
            request_modifier: Optional callable that modifies a Request instance or
                returns a new one. This can be useful for injecting Authentication
                headers and/or signing fully-formed requests (e.g. signing requests
                using AWS SigV4).
                The callable should expect a single argument, which will be an instance
                of :class:`httpx.Request`.
                If the callable returns a `httpx.Request`, that will be used.
                Alternately, the callable may simply modify the provided request object
                and return `None`
            timeout: Optional timeout configuration. Can be:
                - None to disable timeouts
                - float for a default timeout
                - tuple of (connect, read, write, pool) timeouts, each being float or None
                - httpx.Timeout instance for fine-grained control
                See `httpx timeouts <https://www.python-httpx.org/advanced/timeouts/>`__
                for details

        Returns:
            Client: A :class:`Client` instance for this STAPI API
        """
        stapi_io = StapiIO(
            root_url=AnyUrl(url),
            headers=headers,
            parameters=parameters,
            request_modifier=request_modifier,
            timeout=timeout,
        )
        client = Client(stapi_io=stapi_io)

        client.read_links()
        client.read_conformance()

        if not client.has_conforms_to():
            warnings.warn(NoConformsTo())

        return client

    def get_single_link(
        self,
        rel: str | None = None,
        media_type: str | Iterable[str] | None = None,
    ) -> Link | None:
        """Get a single :class:`~stapi_pydantic.Link` instance associated with this object.

        Args:
            rel: Optional relationship filter. If set, only links matching this
                relationship are considered.
            media_type: Optional media type filter. If set, only links matching
                this media type are considered. Can be a single value or an
                iterable of values.

        Returns:
            :class:`~stapi_pydantic.Link` | None: First link that matches ``rel``
                and/or ``media_type``, or else the first link associated with
                this object.
        """
        if rel is None and media_type is None:
            return next(iter(self.links), None)
        if media_type and isinstance(media_type, str):
            media_type = [media_type]
        return next(
            (
                link
                for link in self.links
                if (rel is None or link.rel == rel) and (media_type is None or (link.type or "") in media_type)
            ),
            None,
        )

    def read_links(self) -> None:
        """Read the API links from the root of the STAPI API

        The links are stored in `Client._links`."""
        links = self.stapi_io.read_json("/").get("links", [])
        if links:
            self.links = [Link(**link) for link in links]
        else:
            warnings.warn("No links found in the root of the STAPI API")
            self.links = [
                Link(
                    href=urllib.parse.urljoin(str(self.stapi_io.root_url), link["endpoint"]),
                    rel=link["rel"],
                    method=link["method"],
                )
                for link in DEFAULT_LINKS
            ]

    def read_conformance(self) -> None:
        """Read the API conformance from the root of the STAPI API.

        The conformance is stored in `Client.conforms_to`. This method attempts to read
        from "/conformance" endpoint first, then falls back to the root endpoint "/".

        Note:
            This method silently continues if endpoints return APIError, no exceptions
            are raised.
        """
        conformance: list[str] = []
        for endpoint in ["/conformance", "/"]:
            try:
                conformance = self.stapi_io.read_json(endpoint).get("conformsTo", [])
                break
            except APIError:
                continue

        if conformance:
            self.set_conforms_to(conformance)

    def has_conforms_to(self) -> bool:
        """Whether server contains list of ``"conformsTo"`` URIs

        Return:
            Whether the server contains list of ``"conformsTo"`` URIs
        """
        return bool(self.conforms_to)

    def get_conforms_to(self) -> list[str]:
        """List of ``"conformsTo"`` URIs

        Return:
            List of URIs that the server conforms to
        """
        return self.conforms_to.copy()

    def set_conforms_to(self, conformance_uris: list[str]) -> None:
        """Set list of ``"conformsTo"`` URIs

        Args:
            conformance_uris: URIs indicating what the server conforms to
        """
        self.conforms_to = conformance_uris

    def clear_conforms_to(self) -> None:
        """Clear list of ``"conformsTo"`` urls

        Removes the entire list, so :py:meth:`has_conforms_to` will
        return False after using this method.
        """
        self.conforms_to = []

    def add_conforms_to(self, name: str) -> None:
        """Add ``"conformsTo"`` by name.

        Args:
            name: Name of :py:class:`ConformanceClasses` keys to add.
        """
        conformance_class = ConformanceClasses.get_by_name(name)

        if not self.has_conformance(conformance_class):
            self.set_conforms_to([*self.get_conforms_to(), conformance_class.valid_uri])

    def remove_conforms_to(self, name: str) -> None:
        """Remove ``"conformsTo"`` by name.

        Args:
            name: Name of :py:class:`ConformanceClasses` keys to remove.
        """
        conformance_class = ConformanceClasses.get_by_name(name)

        self.set_conforms_to([uri for uri in self.get_conforms_to() if not re.match(conformance_class.pattern, uri)])

    def has_conformance(self, conformance_class: ConformanceClasses | str) -> bool:
        """Checks whether the API conforms to the given standard.

        This method only checks
        against the ``"conformsTo"`` property from the API landing page and does not
        make any additional calls to a ``/conformance`` endpoint even if the API
        provides such an endpoint.

        Args:
            conformance_class: Either a ConformanceClasses enum member or a string name of a conformance class to check against


        Return:
            Indicates if the API conforms to the given spec or URI.
        """
        if isinstance(conformance_class, str):
            conformance_class = ConformanceClasses.get_by_name(conformance_class)

        return any(re.match(conformance_class.pattern, uri) for uri in self.get_conforms_to())

    def _supports_opportunities(self) -> bool:
        """Check if the API supports opportunities"""
        return self.has_conformance(ConformanceClasses.OPPORTUNITIES)

    def _supports_async_opportunities(self) -> bool:
        """Check if the API supports asynchronous opportunities"""
        return self.has_conformance(ConformanceClasses.ASYNC_OPPORTUNITIES)

    def get_products(self, limit: int | None = None) -> Iterator[Product]:
        """Get all products from this STAPI API

        Returns:
            Iterator[Product]: An iterator of STAPI Products
        """
        products_endpoint = self._get_products_href()

        if limit is None:
            parameters = {}
        else:
            parameters = {"limit": limit}

        products_link = Link(href=products_endpoint, method="GET", body=parameters, rel="")

        products_collection_iterator = self.stapi_io.get_pages(link=products_link, lookup_key="products")
        for products_collection in products_collection_iterator:
            yield from ProductsCollection.model_validate(products_collection).products

    def get_product(self, product_id: str) -> Product:
        """Get a single product from this STAPI API

        Args:
            product_id: The Product ID to get

        Returns:
            Product: A STAPI Product
        """
        product_endpoint = self._get_products_href(product_id)
        product_json = self.stapi_io.read_json(endpoint=product_endpoint)
        return Product.model_validate(product_json)

    def get_product_opportunities(
        self,
        product_id: str,
        date_range: tuple[str, str],
        geometry: dict[str, Any],
        cql2_filter: CQL2Filter | None = None,  # type: ignore[type-arg]
        limit: int = 10,
    ) -> Iterator[Opportunity]:  # type: ignore[type-arg]
        # TODO Update return type after the pydantic model generic type is fixed
        """Get all opportunities for a product from this STAPI API
        Args:
            product_id: The Product ID to get opportunities for
            opportunity_parameters: The parameters for the opportunities

        Returns:
            Iterator[Opportunity]: An iterator of STAPI Opportunities
        """
        product_opportunities_endpoint = self._get_products_href(product_id, subpath="opportunities")

        opportunity_parameters = OpportunityPayload.model_validate(
            {
                "datetime": (
                    datetime.fromisoformat(date_range[0]),
                    datetime.fromisoformat(date_range[1]),
                ),
                "geometry": geometry,
                "filter": cql2_filter,
                "limit": limit,
            }
        )
        opportunities_first_page_link = Link(
            href=product_opportunities_endpoint, method="POST", body=opportunity_parameters.model_dump(), rel=""
        )
        opportunities_first_page_json, next_link = self.stapi_io._get_next_page(
            opportunities_first_page_link, "features"
        )

        if opportunities_first_page_json:
            opportunities_first_page = OpportunityCollection.model_validate(opportunities_first_page_json)  # type:ignore[var-annotated]
            yield from opportunities_first_page.features
        else:
            return

        if next_link is None:
            return

        product_opportunities_json = self.stapi_io.get_pages(link=next_link, lookup_key="features")

        for opportunity_collection in product_opportunities_json:
            yield from OpportunityCollection.model_validate(opportunity_collection).features

    def create_product_order(self, product_id: str, order_parameters: OrderPayload) -> Order:  # type: ignore[type-arg]
        # TODO Update return type after the pydantic model generic type is fixed
        """Create an order for a product

        Args:
            product_id: The Product ID to place an order for
            order_parameters: The parameters for the order
        """
        product_order_endpoint = self._get_products_href(product_id, subpath="orders")
        product_order_json = self.stapi_io.read_json(
            endpoint=product_order_endpoint, method="POST", parameters=order_parameters.model_dump()
        )

        return Order.model_validate(product_order_json)

    def _get_products_href(self, product_id: str | None = None, subpath: str | None = None) -> str:
        """Get the href for the products endpoint

        Args:
            product_id: Optional product ID to get the href for

        Returns:
            str: The href for the products endpoint

        Raises:
            ValueError: When no products link is found in the API
        """
        product_link = self.get_single_link("products")
        if product_link is None:
            raise ValueError("No products link found")
        product_url = URL(str(product_link.href))

        path = None

        if product_id is not None:
            path = f"{product_url.path}/{product_id}"

        if subpath is not None:
            path = f"{path}/{subpath}"

        if path is not None:
            product_url = product_url.copy_with(path=path)

        return str(product_url)

    def get_orders(self, limit: int | None = None) -> Iterator[Order]:  # type: ignore[type-arg]
        # TODO Update return type after the pydantic model generic type is fixed
        """Get orders from this STAPI API

        Args:
            limit: Optional limit on the number of orders to return

        Returns:
            Iterator[Order]: An iterator of STAPI Orders
        """
        orders_endpoint = self._get_orders_href()

        if limit is None:
            parameters = {}
        else:
            parameters = {"limit": limit}

        orders_link = Link(href=orders_endpoint, method="GET", body=parameters, rel="")

        orders_collection_iterator = self.stapi_io.get_pages(link=orders_link, lookup_key="features")
        for orders_collection in orders_collection_iterator:
            yield from OrderCollection.model_validate(orders_collection).features

    def get_order(self, order_id: str) -> Order:  # type: ignore[type-arg]
        # TODO Update return type after the pydantic model generic type is fixed
        """Get a single order from this STAPI API

        Args:
            order_id: The Order ID to get

        Returns:
            Order: A STAPI Order

        Raises:
            ValueError: When the specified order_id does not exist
        """

        order_endpoint = self._get_orders_href(order_id)
        order_json = self.stapi_io.read_json(order_endpoint)

        if order_json is None:
            raise ValueError(f"Order {order_id} not found")

        return Order.model_validate(order_json)

    def _get_orders_href(self, order_id: str | None = None) -> str:
        """Get the href for the orders endpoint

        Args:
            order_id: Optional order ID to get the href for

        Returns:
            The href for the orders endpoint

        Raises:
            ValueError: When no orders link is found in the API
        """

        order_link = self.get_single_link("orders")
        if order_link is None:
            raise ValueError("No orders link found")
        order_url = URL(str(order_link.href))
        if order_id is not None:
            order_url = order_url.copy_with(path=f"{order_url.path}/{order_id}")
        return str(order_url)
