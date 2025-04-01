import json
import logging
from collections.abc import Callable, Iterator
from copy import deepcopy
from typing import Any

import httpx
from httpx import Client as Session
from httpx import Request
from pydantic import AnyUrl
from stapi_pydantic import Link

from pystapi_client._utils import urljoin

from .exceptions import APIError

logger = logging.getLogger(__name__)


class StapiIO:
    def __init__(
        self,
        root_url: AnyUrl,
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
        request_modifier: Callable[[Request], Request | None] | None = None,
        timeout: httpx._types.TimeoutTypes | None = None,
        max_retries: int | None = 5,
    ):
        """Initialize class for API IO

        Args:
            headers : Optional dictionary of headers to include in all requests
            parameters: Optional dictionary of query string parameters to
              include in all requests.
            request_modifier: Optional callable that can be used to modify Request
              objects before they are sent. If provided, the callable receives a
              `request.Request` and must either modify the object directly or return
              a new / modified request instance.
            timeout: Optional float or (float, float) tuple following the semantics
              defined by `Requests
              <https://requests.readthedocs.io/en/latest/api/#main-interface>`__.
            max_retries: The number of times to retry requests. Set to ``None`` to
              disable retries.

        Return:
            StacApiIO : StacApiIO instance
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
        request_modifier: Callable[[Request], Request | None] | None = None,
    ) -> None:
        """Updates this StacApi's headers, parameters, and/or request_modifier.

        Args:
            headers : Optional dictionary of headers to include in all requests
            parameters: Optional dictionary of query string parameters to
              include in all requests.
            request_modifier: Optional callable that can be used to modify Request
              objects before they are sent. If provided, the callable receives a
              `request.Request` and must either modify the object directly or return
              a new / modified request instance.
            timeout: Optional float or (float, float) tuple following the semantics
              defined by `Requests
              <https://requests.readthedocs.io/en/latest/api/#main-interface>`__.
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

        Overwrites the default method for reading text from a URL or file to allow
        :class:`urllib.request.Request` instances as input. This method also raises
        any :exc:`urllib.error.HTTPError` exceptions rather than catching
        them to allow us to handle different response status codes as needed.
        """

        # If "POST" use the body object that and respect the "merge" property.
        if method == "POST":
            parameters = {**(parameters or {})}
        else:
            # parameters are already in the link href
            parameters = {}

        return self.request(href, method=method, headers=headers, parameters=parameters)

    def request(
        self,
        href: str,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Makes a request to an http endpoint

        Args:
            href (str): The request URL
            method (Optional[str], optional): The http method to use, 'GET' or 'POST'.
              Defaults to None, which will result in 'GET' being used.
            headers (Optional[Dict[str, str]], optional): Additional headers to include
                in request. Defaults to None.
            parameters (Optional[Dict[str, Any]], optional): parameters to send with
                request. Defaults to None.

        Raises:
            APIError: raised if the server returns an error response

        Return:
            str: The decoded response from the endpoint
        """
        if method == "POST":
            request = Request(method=method, url=href, headers=headers, json=parameters)
        else:
            params = deepcopy(parameters) or {}
            request = Request(method="GET", url=href, headers=headers, params=params)

        modified = self._req_modifier(request) if self._req_modifier else None

        # Log the request details
        # NOTE can we mask header values?
        msg = f"{request.method} {request.url} Headers: {request.headers}"
        if method == "POST" and hasattr(request, "json"):
            msg += f" Payload: {json.dumps(request.json)}"
        logger.debug(msg)

        try:
            # Send the request
            if modified:
                resp = self.session.send(modified)
            else:
                if method == "POST" and parameters:
                    resp = self.session.post(href, headers=headers, json=parameters)
                else:
                    resp = self.session.get(href, headers=headers, params=parameters)
        except Exception as err:
            logger.debug(err)
            raise APIError(str(err))

        # NOTE what about other successful status codes?
        if resp.status_code != 200:
            raise APIError.from_response(resp)

        try:
            return resp.text
        except Exception as err:
            raise APIError(str(err))

    def _read_json(
        self, endpoint: str, method: str = "GET", parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Read JSON from a URL.

        Args:
            url: The URL to read from
            method: The HTTP method to use
            parameters: Parameters to include in the request

        Returns:
            The parsed JSON response
        """
        href = urljoin(str(self.root_url), endpoint)
        text = self._read_text(href, method=method, parameters=parameters)
        return json.loads(text)  # type: ignore[no-any-return]

    def get_pages(
        self,
        url: str,
        method: str = "GET",
        parameters: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterator that yields dictionaries for each page at a STAPI paging
        endpoint.

        # TODO update endpoint examples

        Return:
            dict[str, Any] : JSON content from a single page
        """
        page = self._read_json(url, method=method, parameters=parameters)
        # TODO update this
        if not (page.get("features") or page.get("collections")):
            return None
        yield page

        next_link = next((link for link in page.get("links", []) if link["rel"] == "next"), None)
        while next_link:
            link = Link.model_validate(next_link)
            page = self._read_json(str(link.href), parameters=parameters)
            if not (page.get("features") or page.get("collections")):
                return None
            yield page

            # get the next link and make the next request
            next_link = next((link for link in page.get("links", []) if link["rel"] == "next"), None)
