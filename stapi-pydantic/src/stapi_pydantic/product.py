from __future__ import annotations

import sys
from enum import Enum
from typing import Any, Literal, TypeAlias

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        pass


from pydantic import AnyHttpUrl, BaseModel, Field

from .constants import STAPI_VERSION
from .shared import Link

Constraints: TypeAlias = BaseModel


class ProviderRole(StrEnum):
    licensor = "licensor"
    producer = "producer"
    processor = "processor"
    host = "host"


class Provider(BaseModel):
    name: str
    description: str | None = None
    roles: list[ProviderRole]
    url: AnyHttpUrl

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
    title: str = ""
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    license: str
    providers: list[Provider] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)

    def with_links(self: Product, links: list[Link] | None = None) -> Product:
        if not links:
            return self

        new = self.model_copy(deep=True)
        new.links.extend(links)
        return new


class ProductsCollection(BaseModel):
    type_: Literal["ProductCollection"] = Field(default="ProductCollection", alias="type")
    links: list[Link] = Field(default_factory=list)
    products: list[Product]
