from typing import Annotated, Any, TypeAlias

from cql2 import Expr
from pydantic import BeforeValidator


def validate(v: dict[str, Any]) -> dict[str, Any]:
    if v:
        # cql2 raises its own exception types, which pydantic does not convert.
        # Re-raise as ValueError so a malformed filter is a 422 rather than a 500.
        try:
            Expr(v).validate()
        except Exception as e:
            raise ValueError(f"invalid CQL2 filter: {e}") from e
    return v


CQL2Filter: TypeAlias = Annotated[
    dict[str, Any],
    BeforeValidator(validate),
]


def cql2_property_names(filter_: dict[str, Any] | None) -> set[str]:
    """Collect all property names referenced in a CQL2 JSON expression."""
    names: set[str] = set()

    def walk(node: Any) -> None:
        match node:
            case {"property": str(name)}:
                names.add(name)
            case dict():
                for value in node.values():
                    walk(value)
            case list():
                for item in node:
                    walk(item)

    walk(filter_ or {})
    return names
