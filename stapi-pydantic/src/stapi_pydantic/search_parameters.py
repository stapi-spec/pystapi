from pydantic import BaseModel, ConfigDict

from .datetime_interval import DatetimeInterval
from .filter import CQL2Filter
from .geometry import Geometry


class SearchParameters(BaseModel):
    """STAPI Search Parameters Object.

    Shared by the Opportunity Request and the Order Request.
    """

    datetime: DatetimeInterval
    geometry: Geometry
    filter: CQL2Filter | None = None

    # vendor extension fields must round-trip through stored orders
    model_config = ConfigDict(extra="allow")
