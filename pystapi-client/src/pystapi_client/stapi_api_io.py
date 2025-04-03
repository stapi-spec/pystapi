import json
import logging
import urllib
import urllib.parse
from collections.abc import Callable, Iterator
from typing import Any

import httpx
from httpx import Client as Session
from httpx import Request
from httpx._types import TimeoutTypes
from pydantic import AnyUrl
from stapi_pydantic import Link

from .exceptions import APIError

logger = logging.getLogger(__name__)


class StapiIO:
    def __init__(
        self,
        root_url: AnyUrl,
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
        request_modifier: Callable[[Request], Request] | None = None,
        timeout: TimeoutTypes | None = None,
        max_retries: int | None = 5,
    ):
        """Initialize class for API IO

        Args:
            root_url: The root URL of the STAPI API
            headers: Optional dictionary of headers to include in all requests
            parameters: Optional dictionary of query string parameters to
              include in all requests.
            request_modifier: Optional callable that can be used to modify Request
              objects before they are sent. If provided, the callable receives a
              `httpx.Request` and must either modify the object directly or return
              a new / modified request instance.
            timeout: Optional timeout configuration. Can be:
              - None to disable timeouts
              - float for a default timeout
              - tuple of (connect, read, write, pool) timeouts, each being float or None
              - httpx.Timeout instance for fine-grained control
              See `httpx timeouts <https://www.python-httpx.org/advanced/timeouts/>`__ for details.
            max_retries: Optional number of times to retry requests. Set to ``None`` to
              disable retries. Defaults to 5.

        Return:
            StapiIO : StapiIO instance
        """
        self.root_url = root_url
        transport = None
        if max_retries is not None:
            transport = httpx.HTTPTransport(retries=max_retries)

        self.session = Session(transport=transport, timeout=timeout)
        self.update(
            headers=headers,
            parameters=parameters,
            request_modifier=request_modifier,
        )

    def update(
        self,
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
        request_modifier: Callable[[Request], Request] | None = None,
    ) -> None:
        """Updates this Stapi's headers, parameters, and/or request_modifier.

        Args:
            headers: Optional dictionary of headers to include in all requests.
            parameters: Optional dictionary of query string parameters to
              include in all requests.
            request_modifier: Optional callable that can be used to modify Request
              objects before they are sent. If provided, the callable receives a
              `httpx.Request` and must either modify the object directly or return
              a new / modified request instance.
        """
        self.session.headers.update(headers or {})
        self.session.params.merge(parameters or {})
        self._req_modifier = request_modifier

    def _read_text(
        self,
        href: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Read text from the given URI.

        Args:
            href: The URL to read from
            method: The HTTP method to use. Defaults to "GET"
            headers: Optional dictionary of additional headers to include in the request
            parameters: Optional dictionary of parameters to include in the request.
                For GET requests, these are added as query parameters.
                For POST requests, these are sent as JSON in the request body


        Returns:
            str: The response text from the server
        """

        return self.request(href, method=method, headers=headers, parameters=parameters if parameters else None)

    def request(
        self,
        href: str,
        method: str,
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Makes a request to an http endpoint

        Args:
            href: The request URL
            method: The http method to use, 'GET' or 'POST'. Defaults to None, which will result in 'GET' being used.
            headers: Additional headers to include in request. Defaults to None.
            parameters: Optional dictionary of parameters to include in the request.
                For GET requests, these are added as query parameters.
                For POST requests, these are sent as JSON in the request body.

        Raises:
            APIError: raised if the server returns an error response

        Returns:
            The decoded response text from the endpoint
        """
        if method == "POST":
            request = Request(method=method, url=href, headers=headers, json=parameters)
        else:
            request = Request(method=method, url=href, headers=headers, params=parameters if parameters else None)

        modified = self._req_modifier(request) if self._req_modifier else request

        # Log the request details
        # NOTE can we mask header values?
        msg = f"{modified.method} {modified.url} Headers: {modified.headers}"
        if method == "POST" and hasattr(modified, "json"):
            msg += f" Payload: {json.dumps(modified.json)}"
        logger.debug(msg)

        try:
            resp = self.session.send(modified)
        except Exception as err:
            logger.debug(err)
            raise APIError.from_response(resp)

        # NOTE what about other successful status codes?
        if resp.status_code != 200:
            raise APIError.from_response(resp)

        try:
            return resp.text
        except Exception as err:
            raise APIError(str(err))

    def read_json(self, endpoint: str, method: str = "GET", parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read JSON from a URL.

        Args:
            endpoint: The URL to read from
            method: The HTTP method to use. Defaults to "GET"
            parameters: Optional dictionary of parameters to include in the request.
                For GET requests, these are added as query parameters.
                For POST requests, these are sent as JSON in the request body

        Returns:
            The parsed JSON response
        """
        href = urllib.parse.urljoin(str(self.root_url), endpoint)

        if method == "POST" and parameters is None:
            parameters = {}

        text = self._read_text(href, method=method, parameters=parameters)
        return json.loads(text)  # type: ignore[no-any-return]

    def _get_next_page(self, link: Link, lookup_key: str) -> tuple[dict[str, Any] | None, Link | None]:
        page = self.read_json(str(link.href), method=link.method or "GET", parameters=link.body)
        next_link = next((link for link in page.get("links", []) if link["rel"] == "next"), None)

        if next_link is not None:
            next_link = Link.model_validate(next_link)

        if page.get(lookup_key):
            return page, next_link

        return None, None

    def get_pages(
        self,
        link: Link,
        lookup_key: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterator that yields dictionaries for each page at a STAPI paging
        endpoint.

        Args:
            url: The URL to read from
            method: The HTTP method to use. Defaults to "GET"
            parameters: Optional dictionary of parameters to include in the request.
                For GET requests, these are added as query parameters.
                For POST requests, these are sent as JSON in the request body
            lookup_key: The key in the response JSON that contains the iterable data.

        # TODO update endpoint examples

        Returns:
            Iterator that yields dictionaries for each page
        """
        if not lookup_key:
            lookup_key = "features"

        first_page, next_link = self._get_next_page(link, lookup_key)

        if first_page is None:
            return None
        yield first_page

        while next_link:
            next_page, next_link = self._get_next_page(next_link, lookup_key)
            if next_page is None:
                return None
            yield next_page
