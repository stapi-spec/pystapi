from pydantic import BaseModel, Field
from stapi_pydantic import Link


class RootResponse(BaseModel):
    id: str
    conformsTo: list[str] = Field(default_factory=list)
    title: str = ""
    description: str = ""
    links: list[Link] = Field(default_factory=list)
