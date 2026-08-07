from typing import Any, Self

from pydantic import BaseModel, RootModel


class JsonSchema(RootModel[dict[str, Any]]):
    """A JSON Schema document."""

    @classmethod
    def from_model(cls, model: type[BaseModel]) -> Self:
        """The JSON Schema describing `model`."""
        return cls(model.model_json_schema())
