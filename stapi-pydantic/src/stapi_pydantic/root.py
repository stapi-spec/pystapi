from pydantic import BaseModel, Field

from .conformance import ConformsTo
from .shared import STAPI_RESPONSE_CONFIG, Link, omitted_when_empty


class RootResponse(BaseModel):
    model_config = STAPI_RESPONSE_CONFIG

    id: str
    conforms_to: ConformsTo = []
    title: str = omitted_when_empty(default="")
    description: str = ""
    links: list[Link] = Field(default_factory=list)
