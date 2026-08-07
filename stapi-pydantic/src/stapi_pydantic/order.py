from __future__ import annotations

import datetime
from collections.abc import Iterator
from enum import StrEnum
from typing import Any, Generic, Literal, TypeVar

from geojson_pydantic.base import _GeoJsonBase
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    field_validator,
)

from .constants import STAPI_VERSION
from .geometry import Geometry
from .search_parameters import SearchParameters
from .shared import STAPI_RESPONSE_CONFIG_ALLOW_EXTRA, Link


class BaseOrderParameters(BaseModel):
    """Minimum-expectations type for order parameters at rest.

    Permissive so stored parameters from any product round-trip.
    """

    model_config = ConfigDict(extra="allow")


class OrderParameters(BaseOrderParameters):
    """Boundary base for product-specific order parameters (strict)."""

    model_config = ConfigDict(extra="forbid")


ORP = TypeVar("ORP", bound=OrderParameters)


class OrderStatusCode(StrEnum):
    received = "received"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"
    scheduled = "scheduled"
    held = "held"
    processing = "processing"
    reserved = "reserved"
    tasked = "tasked"
    user_cancelled = "user_cancelled"
    expired = "expired"
    failed = "failed"


class OrderStatus(BaseModel):
    timestamp: AwareDatetime
    status_code: OrderStatusCode
    reason_code: str | None = None
    reason_text: str | None = None
    links: list[Link] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @classmethod
    def new(
        cls, status_code: OrderStatusCode, reason_code: str | None = None, reason_text: str | None = None
    ) -> OrderStatus:
        """Creates a new order status with timestamp set to now in UTC."""
        return OrderStatus(
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            status_code=status_code,
            reason_code=reason_code,
            reason_text=reason_text,
        )


T = TypeVar("T", bound=OrderStatus)


class OrderStatuses(BaseModel, Generic[T]):
    statuses: list[T]
    links: list[Link] = Field(default_factory=list)


class StoredOrderRequest(BaseModel):
    """Stored form of an Order Request within Order properties.

    order_parameters is typed as BaseOrderParameters because a persisted order
    can no longer be validated against a product's strict OrderParameters model.
    """

    model_config = STAPI_RESPONSE_CONFIG_ALLOW_EXTRA

    search_parameters: SearchParameters
    order_parameters: BaseOrderParameters = Field(default_factory=BaseOrderParameters)


class OrderProperties(BaseModel, Generic[T]):
    model_config = STAPI_RESPONSE_CONFIG_ALLOW_EXTRA

    product_id: str
    created: AwareDatetime
    status: T
    order_request: StoredOrderRequest


# derived from geojson_pydantic.Feature
class Order(_GeoJsonBase, Generic[T]):
    # We need to enforce that orders have an id defined, as that is required to
    # retrieve them via the API
    id: StrictStr
    type: Literal["Feature"] = "Feature"
    stapi_type: Literal["Order"] = "Order"
    stapi_version: str = STAPI_VERSION

    geometry: Geometry = Field(...)
    properties: OrderProperties[T] = Field(...)

    links: list[Link] = Field(default_factory=list)

    __geojson_exclude_if_none__ = {"bbox", "id"}

    @field_validator("geometry", mode="before")
    def set_geometry(cls, geometry: Any) -> Any:
        """set geometry from geo interface or input"""
        if hasattr(geometry, "__geo_interface__"):
            return geometry.__geo_interface__

        return geometry


# derived from geojson_pydantic.FeatureCollection
class OrderCollection(_GeoJsonBase, Generic[T]):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Order[T]]
    links: list[Link] = Field(default_factory=list)
    number_matched: int | None = Field(
        serialization_alias="numberMatched", default=None, exclude_if=lambda x: x is None
    )

    def __iter__(self) -> Iterator[Order[T]]:  # type: ignore [override]
        """iterate over features"""
        return iter(self.features)

    def __len__(self) -> int:
        """return features length"""
        return len(self.features)

    def __getitem__(self, index: int) -> Order[T]:
        """get feature at a given index"""
        return self.features[index]


class OrderRequest(BaseModel, Generic[ORP]):
    """STAPI Order Request Object.

    An omitted order_parameters is equivalent to an empty object, so products
    with required order parameters make the field effectively required.
    """

    search_parameters: SearchParameters
    order_parameters: ORP = Field(default_factory=dict, validate_default=True)

    model_config = ConfigDict(strict=True)
