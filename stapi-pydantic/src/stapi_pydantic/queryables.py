from pydantic import BaseModel, ConfigDict


class Queryables(BaseModel):
    model_config = ConfigDict(extra="allow")
