from enum import StrEnum
from typing import Any

from pydantic import (
    AnyUrl,
    BaseModel,
    Field,
)
from pydantic.json_schema import SkipJsonSchema


class RequestMethod(StrEnum):
    GET = "GET"
    POST = "POST"


class Link(BaseModel):
    href: AnyUrl = Field(description="The location of the resource")
    rel: str = Field(description="Relation type of the link")
    type: str | SkipJsonSchema[None] = Field(default=None, description="The media type of the resource")
    title: str | SkipJsonSchema[None] = Field(default=None, description="Title of the resource")
    method: RequestMethod | SkipJsonSchema[None] = Field(
        default=RequestMethod.GET,
        description="Specifies the HTTP method that the resource expects",
    )
    headers: dict[str, str | list[str]] | SkipJsonSchema[None] = Field(
        default=None,
        description="Object key values pairs they map to headers",
    )
    body: Any = Field(
        default=None,
        description="For POST requests, the resource can specify the HTTP body as a JSON object.",
    )
    merge: bool = Field(
        default=False,
        description=(
            "This is only valid when the server is responding to POST request. "
            "If merge is true, the client is expected to merge the body value into the current request body before "
            "following the link. This avoids passing large post bodies back and forth when following links, "
            "particularly for navigating pages through the POST /search endpoint. "
            "NOTE: To support form encoding it is expected that a client be able to merge in the key value pairs "
            "specified as JSON {'next': 'token'} will become &next=token."
        ),
    )

    # redefining init is a hack to get str type to validate for `href`,
    # as str is ultimately coerced into an AnyUrl automatically anyway
    def __init__(self, href: AnyUrl | str, **kwargs: Any) -> None:
        super().__init__(href=href, **kwargs)
