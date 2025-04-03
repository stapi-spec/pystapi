from enum import Enum
from typing import Any, Literal, TypeVar

try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):
        pass

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .datetime_interval import DatetimeInterval
from .filter import CQL2Filter
from .shared import Link


# Copied and modified from https://github.com/stac-utils/stac-pydantic/blob/main/stac_pydantic/item.py#L11
class OpportunityProperties(BaseModel):
    datetime: DatetimeInterval
    product_id: str
    model_config = ConfigDict(extra="allow")


class OpportunityPayload(BaseModel):
    datetime: DatetimeInterval
    geometry: Geometry
    filter: CQL2Filter | None = None

    next: str | None = None
    limit: int = 10

    model_config = ConfigDict(strict=True)

    def search_body(self) -> dict[str, Any]:
        return self.model_dump(mode="json", include={"datetime", "geometry", "filter"})

    def body(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


G = TypeVar("G", bound=Geometry)
P = TypeVar("P", bound=OpportunityProperties)


class Opportunity(Feature[G, P]):
    type: Literal["Feature"] = "Feature"
    links: list[Link] = Field(default_factory=list)


class OpportunityCollection(FeatureCollection[Opportunity[G, P]]):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    links: list[Link] = Field(default_factory=list)
    id: str | None = None


class OpportunitySearchStatusCode(StrEnum):
    received = "received"
    in_progress = "in_progress"
    failed = "failed"
    canceled = "canceled"
    completed = "completed"


class OpportunitySearchStatus(BaseModel):
    timestamp: AwareDatetime
    status_code: OpportunitySearchStatusCode
    reason_code: str | None = None
    reason_text: str | None = None
    links: list[Link] = Field(default_factory=list)


class OpportunitySearchRecord(BaseModel):
    id: str
    product_id: str
    opportunity_request: OpportunityPayload
    status: OpportunitySearchStatus
    links: list[Link] = Field(default_factory=list)


class OpportunitySearchRecords(BaseModel):
    search_records: list[OpportunitySearchRecord]
    links: list[Link] = Field(default_factory=list)


class Prefer(StrEnum):
    respond_async = "respond-async"
    wait = "wait"
