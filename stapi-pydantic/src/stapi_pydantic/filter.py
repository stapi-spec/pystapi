from typing import Annotated, Any

from cql2 import Expr
from pydantic import BeforeValidator


def validate(v: dict[str, Any]) -> dict[str, Any]:
    if v:
        expr = Expr(v)
        expr.validate()
    return v


type CQL2Filter = Annotated[
    dict,
    BeforeValidator(validate),
]
