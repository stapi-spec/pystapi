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

OPEN_END = ".."


def _check_order(start: datetime, end: datetime) -> None:
    if end < start:
        raise ValueError("end before start")


def _parse_end(value: str) -> datetime | None:
    if value in ("", OPEN_END):
        return None
    return datetime.fromisoformat(value)


def validate_bounded_before(
    value: str | tuple[datetime, datetime],
) -> tuple[datetime, datetime]:
    if isinstance(value, str):
        start, end = value.split("/", 1)
        return (datetime.fromisoformat(start), datetime.fromisoformat(end))
    return value


def validate_bounded_after(value: tuple[datetime, datetime]) -> tuple[datetime, datetime]:
    _check_order(*value)
    return value


def validate_before(
    value: str | tuple[datetime | None, datetime | None],
) -> tuple[datetime | None, datetime | None]:
    if isinstance(value, str):
        start, end = value.split("/", 1)
        return (_parse_end(start), _parse_end(end))
    return value


def validate_after(
    value: tuple[datetime | None, datetime | None],
) -> tuple[datetime | None, datetime | None]:
    if value[0] is None and value[1] is None:
        raise ValueError("only singly-open intervals are allowed")
    if value[0] is not None and value[1] is not None:
        _check_order(value[0], value[1])
    return value


def serialize_bounded(
    value: tuple[datetime, datetime],
    serializer: Callable[[tuple[datetime, datetime]], tuple[str, str]],
) -> str:
    del serializer  # unused
    return f"{value[0].isoformat()}/{value[1].isoformat()}"


def serialize(
    value: tuple[datetime | None, datetime | None],
    serializer: Callable[[tuple[datetime | None, datetime | None]], tuple[str, str]],
) -> str:
    del serializer  # unused
    start = OPEN_END if value[0] is None else value[0].isoformat()
    end = OPEN_END if value[1] is None else value[1].isoformat()
    return f"{start}/{end}"


# Both ends bounded: for a window the provider has already determined, e.g. an
# Opportunity's datetime property.
BoundedDatetimeInterval = Annotated[
    tuple[AwareDatetime, AwareDatetime],
    BeforeValidator(validate_bounded_before),
    AfterValidator(validate_bounded_after),
    WrapSerializer(serialize_bounded, return_type=str),
    WithJsonSchema({"type": "string"}),
]

# The general STAPI interval: open (via ``..`` or an empty string) on at most one
# end, for intervals that express a query rather than a result.
DatetimeInterval = Annotated[
    tuple[AwareDatetime | None, AwareDatetime | None],
    BeforeValidator(validate_before),
    AfterValidator(validate_after),
    WrapSerializer(serialize, return_type=str),
    WithJsonSchema({"type": "string"}),
]
