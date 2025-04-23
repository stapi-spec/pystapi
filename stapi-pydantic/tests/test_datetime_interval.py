import pytest
from stapi_pydantic import DatetimeInterval


def test_valid_datetime_intervals() -> None:
    """Test the datetime interval validator."""
    dt1 = DatetimeInterval.__metadata__[0].func("2025-04-01T00:00:00Z/2025-04-01T23:59:59Z")
    _ = DatetimeInterval.__metadata__[1].func(dt1)
    dt2 = DatetimeInterval.__metadata__[0].func("2025-04-01T00:00:00Z/..")
    _ = DatetimeInterval.__metadata__[1].func(dt2)
    dt3 = DatetimeInterval.__metadata__[0].func("../2025-04-01T23:59:59Z")
    _ = DatetimeInterval.__metadata__[1].func(dt3)
    dt4 = DatetimeInterval.__metadata__[0].func("../..")
    _ = DatetimeInterval.__metadata__[1].func(dt4)


def test_invalid_datetime_intervals() -> None:
    """Test the datetime interval validator."""
    with pytest.raises(ValueError, match="end before start"):
        dt1 = DatetimeInterval.__metadata__[0].func("2025-04-01T00:00:00Z/2025-03-01T23:59:59Z")
        _ = DatetimeInterval.__metadata__[1].func(dt1)

