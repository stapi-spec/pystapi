from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Generic, Literal, TypeVar

from geojson_pydantic import Feature, FeatureCollection
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from typing_extensions import TypeVar as DefaultTypeVar

from .constants import STAPI_VERSION
from .datetime_interval import BoundedDatetimeInterval
from .geometry import Geometry
from .search_parameters import SearchParameters
from .shared import (
    STAPI_RESPONSE_CONFIG,
    UNSET_BBOX,
    ComputedBBox,
    DerivedCollectionBBox,
    DerivedItemBBox,
    Link,
    NumberMatched,
    OptionalBBox,
    StapiGenericModel,
    omitted_when_none,
)


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


class Opportunity(Feature[G, P], StapiGenericModel, DerivedItemBBox):
    model_config = STAPI_RESPONSE_CONFIG

    id: str | None = omitted_when_none()
    type: Literal["Feature"] = "Feature"
    stapi_type: Literal["Opportunity"] = "Opportunity"
    stapi_version: str = STAPI_VERSION
    geometry: G = Field(...)
    bbox: ComputedBBox = UNSET_BBOX
    properties: P = Field(...)
    links: list[Link] = Field(default_factory=list)


class OpportunityCollection(FeatureCollection[Opportunity[G, P]], StapiGenericModel, DerivedCollectionBBox):
    model_config = STAPI_RESPONSE_CONFIG

    type: Literal["FeatureCollection"] = "FeatureCollection"
    stapi_type: Literal["OpportunityCollection"] = "OpportunityCollection"
    stapi_version: str = STAPI_VERSION
    bbox: OptionalBBox = None
    links: list[Link] = Field(default_factory=list)
    id: str | None = omitted_when_none()
    number_matched: NumberMatched = None


class OpportunitySearchStatusCode(StrEnum):
    received = "received"
    in_progress = "in_progress"
    failed = "failed"
    cancelled = "cancelled"
    completed = "completed"


AnySearchStatusCode = Annotated[OpportunitySearchStatusCode | str, Field(union_mode="left_to_right")]

SearchStatusCode = DefaultTypeVar("SearchStatusCode", bound=str, default=AnySearchStatusCode)


class OpportunitySearchStatus(StapiGenericModel, Generic[SearchStatusCode]):
    """A search record status; parameterize with a StrEnum
    (``OpportunitySearchStatus[MyCodes]``) to constrain status_code to an
    implementation-defined set."""

    model_config = STAPI_RESPONSE_CONFIG

    timestamp: AwareDatetime
    status_code: SearchStatusCode
    reason_code: str | None = omitted_when_none()
    reason_text: str | None = omitted_when_none()
    links: list[Link] = Field(default_factory=list)


class OpportunitySearchRecord(BaseModel):
    model_config = STAPI_RESPONSE_CONFIG

    id: str
    product_id: str
    search_parameters: SearchParameters
    status: OpportunitySearchStatus
    stapi_type: Literal["OpportunitySearchRecord"] = "OpportunitySearchRecord"
    stapi_version: str = STAPI_VERSION
    links: list[Link] = Field(default_factory=list)


class OpportunitySearchRecordCollection(BaseModel):
    model_config = STAPI_RESPONSE_CONFIG

    stapi_type: Literal["OpportunitySearchRecordCollection"] = "OpportunitySearchRecordCollection"
    stapi_version: str = STAPI_VERSION
    records: list[OpportunitySearchRecord]
    links: list[Link] = Field(default_factory=list)
    number_matched: NumberMatched = None


class OpportunitySearchStatusCollection(BaseModel):
    model_config = STAPI_RESPONSE_CONFIG

    stapi_type: Literal["OpportunitySearchStatusCollection"] = "OpportunitySearchStatusCollection"
    stapi_version: str = STAPI_VERSION
    statuses: list[OpportunitySearchStatus]
    links: list[Link] = Field(default_factory=list)
    number_matched: NumberMatched = None


class Prefer(StrEnum):
    respond_async = "respond-async"
    wait = "wait"
