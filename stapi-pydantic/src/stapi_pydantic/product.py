from enum import StrEnum
from typing import Any, Literal, Self, TypeAlias

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

from .constants import STAPI_VERSION
from .shared import Link

Constraints: TypeAlias = BaseModel


class ProviderRole(StrEnum):
    producer = "producer"
    licensor = "licensor"
    processor = "processor"
    host = "host"


class Provider(BaseModel):
    name: str
    description: str | SkipJsonSchema[None] = None
    roles: list[ProviderRole] | SkipJsonSchema[None] = None
    url: AnyHttpUrl | SkipJsonSchema[None] = None

    # redefining init is a hack to get str type to validate for `url`,
    # as str is ultimately coerced into an AnyHttpUrl automatically anyway
    def __init__(self, url: AnyHttpUrl | str, **kwargs: Any) -> None:
        super().__init__(url=url, **kwargs)


class Product(BaseModel):
    type_: Literal["Collection"] = Field(default="Collection", alias="type")
    stapi_type: Literal["Product"] = "Product"
    stapi_version: str = STAPI_VERSION
    conformsTo: list[str] = Field(default_factory=list)
    id: str
    title: str | SkipJsonSchema[None] = None
    description: str
    keywords: list[str] | SkipJsonSchema[None] = None
    license: str
    providers: list[Provider] | SkipJsonSchema[None] = None
    links: list[Link]

    def with_links(self, links: list[Link] | None = None) -> Self:
        if not links:
            return self

        new = self.model_copy(deep=True)
        new.links.extend(links)
        return new


class ProductsCollection(BaseModel):
    links: list[Link]
    products: list[Product] = Field(
        description=(
            "STAPI Product objects are represented in JSON format and are very flexible. "
            "Any JSON object that contains all the required fields is a valid STAPI Product. "
            "A Product object contains a minimal set of required properties to be valid and can be extended "
            "through the use of queryables and parameters."
        )
    )
