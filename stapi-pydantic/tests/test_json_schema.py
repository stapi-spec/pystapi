from pydantic import TypeAdapter
from stapi_pydantic.datetime_interval import DatetimeInterval


def test_datetime_interval() -> None:
    assert TypeAdapter(DatetimeInterval).json_schema() == {"type": "string"}
