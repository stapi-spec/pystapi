from pydantic import BaseModel, Field


class Conformance(BaseModel):
    conforms_to: list[str] = Field(default_factory=list, serialization_alias="conformsTo")
