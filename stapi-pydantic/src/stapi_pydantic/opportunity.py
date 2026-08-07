from enum import StrEnum
from typing import Any, Literal, TypeVar

from geojson_pydantic import Feature, FeatureCollection
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .datetime_interval import BoundedDatetimeInterval
from .geometry import Geometry
from .search_parameters import SearchParameters
from .shared import Link


# Copied and modified from https://github.com/stac-utils/stac-pydantic/blob/main/stac_pydantic/item.py#L11
class OpportunityProperties(BaseModel):
    datetime: BoundedDatetimeInterval
    product_id: str
    model_config = ConfigDict(extra="allow")


class OpportunityRequest(BaseModel):
    """STAPI Opportunity Request Object.

    Carries the same ``search_parameters`` as an Order Request, which
    additionally supplies ``order_parameters``. ``next`` and ``limit`` page a
    search and have no Order Request equivalent.
    """

    search_parameters: SearchParameters

    next: str | None = None
    # No default page size: `None` means the request named none, leaving the
    # server to supply its own, rather than a number this library picked. The
    # lower bound is the spec's; it publishes no upper one, so a server clamps
    # rather than rejects.
    limit: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(strict=True)

    def search_body(self) -> dict[str, Any]:
        return self.model_dump(mode="json", include={"search_parameters"})

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
    cancelled = "cancelled"
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
    opportunity_request: OpportunityRequest
    status: OpportunitySearchStatus
    links: list[Link] = Field(default_factory=list)


class OpportunitySearchRecords(BaseModel):
    search_records: list[OpportunitySearchRecord]
    links: list[Link] = Field(default_factory=list)


class Prefer(StrEnum):
    respond_async = "respond-async"
    wait = "wait"
