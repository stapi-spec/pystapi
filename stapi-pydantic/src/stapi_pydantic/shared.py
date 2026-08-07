from typing import Any

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
)


def omitted_when_none(**kwargs: Any) -> Any:
    """A spec-OPTIONAL field that is omitted rather than serialized as null.

    `exclude_if` also keeps the field out of the serialization-required set
    that `json_schema_serialization_defaults_required` would otherwise put it
    in.
    """
    return Field(default=None, exclude_if=lambda v: v is None, **kwargs)


class Link(BaseModel):
    href: AnyUrl
    rel: str
    type: str | None = omitted_when_none()
    title: str | None = omitted_when_none()
    method: str | None = omitted_when_none()
    headers: dict[str, str | list[str]] | None = omitted_when_none()
    body: Any = omitted_when_none()

    model_config = ConfigDict(extra="allow")

    # redefining init is a hack to get str type to validate for `href`,
    # as str is ultimately coerced into an AnyUrl automatically anyway
    # `href` must carry a default: without one, pydantic routes validation
    # through this __init__ and a payload missing `href` raises TypeError from
    # argument binding rather than yielding a ValidationError.
    def __init__(self, href: Any = None, **kwargs: Any) -> None:
        super().__init__(href=href if isinstance(href, AnyUrl) else str(href), **kwargs)
