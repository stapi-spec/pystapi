from functools import cache

from pydantic import BaseModel, ConfigDict


class Queryables(BaseModel):
    model_config = ConfigDict(extra="allow")

    @classmethod
    @cache
    def required_property_names(cls) -> frozenset[str]:
        """Names of the queryables a filter must supply a predicate for.

        Taken from the published queryables JSON Schema, so a client is held to
        exactly the set it can see.
        """
        return frozenset(cls.model_json_schema().get("required", []))
