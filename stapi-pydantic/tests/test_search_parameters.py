import pytest
from pydantic import ValidationError
from stapi_pydantic import STAPI_VERSION, SearchParameters

GEOMETRY = {"type": "Point", "coordinates": [13.4, 52.5]}


def test_stapi_version_is_0_2_0() -> None:
    assert STAPI_VERSION == "0.2.0"


def test_search_parameters_minimal() -> None:
    sp = SearchParameters.model_validate(
        {
            "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
            "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
        }
    )
    assert sp.filter is None


@pytest.mark.parametrize("interval", ["2024-04-18T10:56:00Z/..", "2024-04-18T10:56:00Z/"])
def test_search_parameters_open_end(interval: str) -> None:
    sp = SearchParameters.model_validate({"datetime": interval, "geometry": GEOMETRY})
    assert sp.datetime[0] is not None
    assert sp.datetime[1] is None
    assert sp.model_dump(mode="json")["datetime"] == "2024-04-18T10:56:00+00:00/.."


@pytest.mark.parametrize("interval", ["../2024-04-25T10:56:00+01:00", "/2024-04-25T10:56:00+01:00"])
def test_search_parameters_open_start(interval: str) -> None:
    sp = SearchParameters.model_validate({"datetime": interval, "geometry": GEOMETRY})
    assert sp.datetime[0] is None
    assert sp.datetime[1] is not None
    assert sp.model_dump(mode="json")["datetime"] == "../2024-04-25T10:56:00+01:00"


@pytest.mark.parametrize("interval", ["../..", "/", "../", "/.."])
def test_search_parameters_doubly_open_interval_rejected(interval: str) -> None:
    with pytest.raises(ValidationError):
        SearchParameters.model_validate({"datetime": interval, "geometry": GEOMETRY})


def test_search_parameters_end_before_start_rejected() -> None:
    with pytest.raises(ValidationError, match="end before start"):
        SearchParameters.model_validate({"datetime": "2024-04-25T10:56:00Z/2024-04-18T10:56:00Z", "geometry": GEOMETRY})


def test_search_parameters_with_filter() -> None:
    sp = SearchParameters.model_validate(
        {
            "datetime": "2024-04-18T10:56:00Z/2024-04-25T10:56:00Z",
            "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
            "filter": {"op": ">=", "args": [{"property": "gsd"}, 1.0]},
        }
    )
    assert sp.filter is not None
