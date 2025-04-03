from pydantic import BaseModel, Field


class Conformance(BaseModel):
    conforms_to: list[str] = Field(serialization_alias="conformsTo")
