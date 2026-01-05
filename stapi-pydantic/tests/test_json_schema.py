from pydantic import TypeAdapter
from stapi_pydantic import DatetimeInterval


def test_datetime_interval() -> None:
    assert TypeAdapter(DatetimeInterval).json_schema() == {"type": "string"}
