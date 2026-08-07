import pytest
from pydantic import TypeAdapter, ValidationError
from stapi_pydantic import CQL2Filter
from stapi_pydantic.filter import cql2_property_names

FILTER = TypeAdapter(CQL2Filter)


def test_malformed_filter_is_a_validation_error() -> None:
    # cql2 raises its own exception types, which pydantic does not convert, so a
    # malformed filter has to be re-raised as a ValueError to be a 422 not a 500
    # `=` takes two arguments; cql2 parses this but rejects it on validation
    with pytest.raises(ValidationError, match="invalid CQL2 filter"):
        FILTER.validate_python({"op": "=", "args": [{"property": "platform"}]})


def test_valid_filter_is_accepted() -> None:
    filter_ = {"op": "=", "args": [{"property": "platform"}, "umbra"]}
    assert FILTER.validate_python(filter_) == filter_


def test_property_names_empty() -> None:
    assert cql2_property_names(None) == set()
    assert cql2_property_names({}) == set()


def test_property_names_nested() -> None:
    filter_ = {
        "op": "and",
        "args": [
            {"op": ">=", "args": [{"property": "sar:resolution_range"}, 1.0]},
            {"op": "=", "args": [{"property": "platform"}, "umbra"]},
        ],
    }
    assert cql2_property_names(filter_) == {"sar:resolution_range", "platform"}
