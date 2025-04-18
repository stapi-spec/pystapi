from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BeforeValidator,
    WithJsonSchema,
    WrapSerializer,
)

_DatetimeTuple = tuple[datetime | None, datetime | None]


def validate_before(value: str | _DatetimeTuple) -> _DatetimeTuple:
    if isinstance(value, str):
        start_str, end_str = value.split("/", 1)
        start = None if start_str == ".." else datetime.fromisoformat(start_str)
        end = None if end_str == ".." else datetime.fromisoformat(end_str)
        value = (start, end)
    return value


def validate_after(value: _DatetimeTuple) -> _DatetimeTuple:
    # None/date & date/None are always valid
    if value[1] and value[0] and value[1] < value[0]:
        raise ValueError("end before start")
    return value


def serialize(
    value: _DatetimeTuple,
    serializer: Callable[[_DatetimeTuple], tuple[str, str]],
) -> str:
    del serializer  # unused
    start = value[0].isoformat() if value[0] else ".."
    end = value[1].isoformat() if value[1] else ".."
    return f"{start}/{end}"


DatetimeInterval = Annotated[
    tuple[AwareDatetime | None, AwareDatetime | None],
    BeforeValidator(validate_before),
    AfterValidator(validate_after),
    WrapSerializer(serialize, return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]
