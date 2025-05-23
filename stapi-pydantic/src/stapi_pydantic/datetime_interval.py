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


def validate_before(
    value: str | tuple[datetime, datetime],
) -> tuple[datetime, datetime]:
    if isinstance(value, str):
        start, end = value.split("/", 1)
        return (datetime.fromisoformat(start), datetime.fromisoformat(end))
    return value


def validate_after(value: tuple[datetime, datetime]) -> tuple[datetime, datetime]:
    if value[1] < value[0]:
        raise ValueError("end before start")
    return value


def serialize(
    value: tuple[datetime, datetime],
    serializer: Callable[[tuple[datetime, datetime]], tuple[str, str]],
) -> str:
    del serializer  # unused
    return f"{value[0].isoformat()}/{value[1].isoformat()}"


DatetimeInterval = Annotated[
    tuple[AwareDatetime, AwareDatetime],
    BeforeValidator(validate_before),
    AfterValidator(validate_after),
    WrapSerializer(serialize, return_type=str),
    WithJsonSchema({"type": "string"}),
]
