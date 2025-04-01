from pydantic import BaseModel, Field

from .shared import Link


class RootResponse(BaseModel):
    id: str
    conformsTo: list[str] = Field(default_factory=list)
    title: str = ""
    description: str = ""
    links: list[Link] = Field(default_factory=list)
