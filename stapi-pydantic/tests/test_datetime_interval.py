from stapi_pydantic import DatetimeInterval


def test_datetime_interval() -> None:
    """Test the datetime interval validator."""
    dt1 = DatetimeInterval.__metadata__[0].func("2025-04-01T00:00:00Z/2025-04-01T23:59:59Z")
    dt2 = DatetimeInterval.__metadata__[0].func("2025-04-01T00:00:00Z/..")
    dt3 = DatetimeInterval.__metadata__[0].func("../2025-04-01T23:59:59Z")
    _ = DatetimeInterval.__metadata__[1].func(dt1)
    _ = DatetimeInterval.__metadata__[1].func(dt2)
    _ = DatetimeInterval.__metadata__[1].func(dt3)
