from enum import Enum
from collections.abc import Iterator
from typing import Any, Generic, Literal, TypeVar

try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):
        pass

from geojson_pydantic.base import _GeoJsonBase
from geojson_pydantic.geometries import Geometry
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    field_validator,
)

from .constants import STAPI_VERSION
from .datetime_interval import DatetimeInterval
from .filter import CQL2Filter
from .opportunity import OpportunityProperties
from .shared import Link

Props = TypeVar("Props", bound=dict[str, Any] | BaseModel)
Geom = TypeVar("Geom", bound=Geometry)


class OrderParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")


OPP = TypeVar("OPP", bound=OpportunityProperties)
ORP = TypeVar("ORP", bound=OrderParameters)


class OrderStatusCode(StrEnum):
    received = "received"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    canceled = "canceled"
    scheduled = "scheduled"
    held = "held"
    processing = "processing"
    reserved = "reserved"
    tasked = "tasked"
    user_canceled = "user_canceled"


class OrderStatus(BaseModel):
    timestamp: AwareDatetime
    status_code: OrderStatusCode
    reason_code: str | None = None
    reason_text: str | None = None
    links: list[Link] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class OrderStatuses[T: OrderStatus](BaseModel):
    statuses: list[T]
    links: list[Link] = Field(default_factory=list)


class OrderSearchParameters(BaseModel):
    datetime: DatetimeInterval
    geometry: Geometry
    # TODO: validate the CQL2 filter?
    filter: CQL2Filter | None = None


class OrderProperties[T: OrderStatus](BaseModel):
    product_id: str
    created: AwareDatetime
    status: T

    search_parameters: OrderSearchParameters
    opportunity_properties: dict[str, Any]
    order_parameters: dict[str, Any]

    model_config = ConfigDict(extra="allow")


# derived from geojson_pydantic.Feature
class Order[T: OrderStatus](_GeoJsonBase):
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
class OrderCollection[T: OrderStatus](_GeoJsonBase):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Order[T]]
    links: list[Link] = Field(default_factory=list)

    def __iter__(self) -> Iterator[Order[T]]:  # type: ignore [override]
        """iterate over features"""
        return iter(self.features)

    def __len__(self) -> int:
        """return features length"""
        return len(self.features)

    def __getitem__(self, index: int) -> Order[T]:
        """get feature at a given index"""
        return self.features[index]


class OrderPayload(BaseModel, Generic[ORP]):
    datetime: DatetimeInterval
    geometry: Geometry
    # TODO: validate the CQL2 filter?
    filter: CQL2Filter | None = None

    order_parameters: ORP

    model_config = ConfigDict(strict=True)
