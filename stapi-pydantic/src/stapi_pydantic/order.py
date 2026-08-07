from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Annotated, Any, Generic, Literal, Self, TypeVar, cast

from geojson_pydantic import Feature, FeatureCollection
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
)
from typing_extensions import TypeVar as DefaultTypeVar

from .constants import STAPI_VERSION
from .geometry import Geometry
from .search_parameters import SearchParameters
from .shared import STAPI_RESPONSE_CONFIG, STAPI_RESPONSE_CONFIG_ALLOW_EXTRA, Link, omitted_when_none


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


AnyOrderStatusCode = Annotated[OrderStatusCode | str, Field(union_mode="left_to_right")]

StatusCode = DefaultTypeVar("StatusCode", bound=str, default=AnyOrderStatusCode)


class OrderStatus(BaseModel, Generic[StatusCode]):
    """An order status; parameterize with a StrEnum (``OrderStatus[MyCodes]``)
    to constrain status_code to an implementation-defined set."""

    timestamp: AwareDatetime
    status_code: StatusCode
    reason_code: str | None = omitted_when_none()
    reason_text: str | None = omitted_when_none()
    links: list[Link] = Field(default_factory=list)

    model_config = STAPI_RESPONSE_CONFIG_ALLOW_EXTRA

    @classmethod
    def new(
        cls, status_code: OrderStatusCode | str, reason_code: str | None = None, reason_text: str | None = None
    ) -> Self:
        """Creates a new order status with timestamp set to now in UTC."""
        return cls(
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            # the accepted codes are whatever cls was parameterized with, which
            # the signature can't name; validation enforces it.
            status_code=cast(StatusCode, status_code),
            reason_code=reason_code,
            reason_text=reason_text,
        )


# Defaulted so an unparameterized Order resolves to OrderStatus itself rather
# than the bound OrderStatus[Any], which would emit a second, unconstrained
# OrderStatus schema.
T = DefaultTypeVar("T", bound=OrderStatus[Any], default=OrderStatus)


class OrderStatusCollection(BaseModel, Generic[T]):
    model_config = STAPI_RESPONSE_CONFIG

    stapi_type: Literal["OrderStatusCollection"] = "OrderStatusCollection"
    stapi_version: str = STAPI_VERSION
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


class Order(Feature[Geometry, OrderProperties[T]], Generic[T]):
    model_config = STAPI_RESPONSE_CONFIG

    # We need to enforce that orders have an id defined, as that is required to
    # retrieve them via the API
    id: StrictStr
    type: Literal["Feature"] = "Feature"
    stapi_type: Literal["Order"] = "Order"
    stapi_version: str = STAPI_VERSION

    geometry: Geometry = Field(...)
    properties: OrderProperties[T] = Field(...)

    links: list[Link] = Field(default_factory=list)


class OrderCollection(FeatureCollection[Order[T]], Generic[T]):
    model_config = STAPI_RESPONSE_CONFIG

    type: Literal["FeatureCollection"] = "FeatureCollection"
    stapi_type: Literal["OrderCollection"] = "OrderCollection"
    stapi_version: str = STAPI_VERSION
    links: list[Link] = Field(default_factory=list)
    number_matched: int | None = Field(
        serialization_alias="numberMatched", default=None, exclude_if=lambda x: x is None
    )


class OrderRequest(BaseModel, Generic[ORP]):
    """STAPI Order Request Object.

    An omitted order_parameters is equivalent to an empty object, so products
    with required order parameters make the field effectively required.
    """

    search_parameters: SearchParameters
    order_parameters: ORP = Field(default_factory=dict, validate_default=True)

    model_config = ConfigDict(strict=True)
