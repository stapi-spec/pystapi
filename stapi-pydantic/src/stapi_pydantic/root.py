from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

from .shared import Link


class RootResponse(BaseModel):
    conforms_to: list[str] = Field(serialization_alias="conformsTo")
    id: str
    title: str | SkipJsonSchema[None] = None
    description: str
    links: list[Link]
