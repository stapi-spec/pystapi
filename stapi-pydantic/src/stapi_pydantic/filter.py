from typing import Annotated, Any, TypeAlias

from cql2 import Expr
from pydantic import BeforeValidator


def validate(v: dict[str, Any]) -> dict[str, Any]:
    if v:
        expr = Expr(v)
        expr.validate()
    return v


CQL2Filter: TypeAlias = Annotated[
    dict,
    BeforeValidator(validate),
]
