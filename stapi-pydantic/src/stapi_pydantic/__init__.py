from __future__ import annotations

import datetime
from typing import Any, Literal

from geojson_pydantic.geometries import Geometry
from pydantic import BaseModel


class Product(BaseModel):
    """A STAPI Product is remote sensing data or derived insights with spatio-temporal components that can deliver value to the user."""

    type: Literal["Product"]
    """Must be set to Product to be a valid Product."""

    id: str
    """Identifier for the Product that is unique across the provider."""

    conformsTo: list[str] | None = None
    """Conformance classes that apply to the product specifically."""

    title: str | None = None
    """A short descriptive one-line title for the Product."""

    description: str
    """Detailed multi-line description to fully explain the product.
    
    CommonMark 0.29 syntax MAY be used for rich text representation."""

    keywords: list[str] | None = None
    """List of keywords describing the Product."""

    license: str
    """Product's license(s), either a SPDX License identifier, various if multiple licenses apply or proprietary for all other cases."""

    providers: list[Provider] | None = None
    """A list of providers, which may include all organizations capturing or processing the data or the hosting provider.

    Providers should be listed in chronological order with the most recent provider being the last element of the list."""

    links: list[Link]
    """A list of references to other documents."""


class Provider(BaseModel):
    """The object provides information about a provider.

    A provider is any of the organizations that captures or processes the content of the Product and therefore influences the data offered by this Product.
    May also include information about the final storage provider hosting the data."""

    name: str
    """The name of the organization or the individual."""

    description: str | None = None
    """Multi-line description to add further provider information such as processing details for processors and producers, hosting details for hosts or basic contact information.
    
    CommonMark 0.29 syntax MAY be used for rich text representation."""

    roles: list[str] | None = None
    """Role of the provider.
    
    Set to producer or reseller"""

    url: str | None = None
    """Homepage on which the provider describes the dataset and publishes contact information."""


class Request(BaseModel):
    """A request for the provider to collect or otherwise gather data, or to provide information about an opportunity."""

    datetime: str
    """Time interval with a solidus (forward slash, /) separator, using RFC 3339 datetime, empty string, or .. values."""

    productId: str
    """Product identifier.
    
    The ID should be unique and is a reference to the parameters which can be used in the parameters field."""

    geometry: Geometry
    """Provide a Geometry that the tasked data must be within."""

    filter: dict[str, Any] | None = None
    """A set of additional parameters in CQL2 JSON based on the parameters exposed in the product."""


class Opportunity(BaseModel):
    """An opportunity to collect data."""

    type: Literal["Feature"]
    """Type of the GeoJSON Object. MUST be set to Feature."""

    id: str | None = None
    """Provider identifier.
    
    This is not required, unless the provider tracks user requests and state for opportunities."""

    geometry: Geometry | None
    """ Defines the full footprint of the asset represented by this item, formatted according to RFC 7946, section 3.1.

    The footprint should be the default GeoJSON geometry, though additional geometries can be included.
    Coordinates are specified in Longitude/Latitude or Longitude/Latitude/Elevation based on WGS 84."""

    bbox: list[float] | None = None
    """REQUIRED if geometry is not null.
    
    Bounding Box of the asset represented by this Item, formatted according to RFC 7946, section 5."""

    properties: Properties
    """A dictionary of additional metadata for the Item."""

    links: list[Link] = []
    """List of link objects to resources and related URLs.

    There must be a rel=create-order link that allows the user to Order this opportunity."""


class Properties(BaseModel):
    """Additional metadata fields can be added to the GeoJSON Object Properties that describe the Opportunity in more detail for the user."""

    datetime: str
    """Datetime field is a ISO8601 Time Interval"""

    product_id: str
    """Product identifier.
    
    The ID should be unique and is a reference to the parameters which can be used in the parameters field."""


class Order(BaseModel):
    """An order"""

    id: str
    """Unique provider generated order ID"""

    user: str
    """User or organization ID ?"""

    created: datetime.datetime
    """When the order was created"""

    status: Status
    """Current Order Status object"""

    links: list[Link] = []
    """Links will be very provider specific."""


class Status(BaseModel):
    """Order status"""

    timestamp: datetime.datetime
    """ISO 8601 timestamp for the order status"""

    status_code: str
    """Enumerated status code"""

    reason_code: str | None = None
    """Enumerated reason code for why the status was set"""

    reason_text: str | None = None
    """Textual description for why the status was set"""

    links: list[Link] = []
    """List of references to documents, such as delivered asset, processing log, delivery manifest, etc."""


class Link(BaseModel):
    """Links will be very provider specific."""

    href: str
    """The actual link in the format of an URL.
    
    Relative and absolute links are both allowed. Trailing slashes are significant."""

    rel: str
    """Relationship between the current document and the linked document.
    
    See chapter "Relation types" for more information."""

    type: str | None = None
    """Media type of the referenced entity."""

    title: str | None = None
    """A human readable title to be used in rendered displays of the link."""

    method: str | None = None
    """The HTTP method that shall be used for the request to the target resource, in uppercase.
    
    GET by default"""

    headers: dict[str, str | list[str]] | None = None
    """The HTTP headers to be sent for the request to the target resource."""
