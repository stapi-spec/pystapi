from pydantic import BaseModel, TypeAdapter
from stapi_pydantic import JsonSchema
from stapi_pydantic.datetime_interval import DatetimeInterval


def test_datetime_interval() -> None:
    assert TypeAdapter(DatetimeInterval).json_schema() == {"type": "string"}


class _Queryables(BaseModel):
    off_nadir: float


def test_from_model_derives_the_schema() -> None:
    assert JsonSchema.from_model(_Queryables).model_dump() == _Queryables.model_json_schema()


def test_json_schema_round_trips() -> None:
    """A published document can be read back, which a model class could not."""
    schema = JsonSchema.from_model(_Queryables)

    assert JsonSchema.model_validate(schema.model_dump()) == schema


def test_json_schema_publishes_an_object_component() -> None:
    """The endpoints returning it `$ref` this, so it has to describe an object."""
    assert JsonSchema.model_json_schema()["type"] == "object"
