from enum import StrEnum
from typing import Any, Literal, Optional, Self

from pydantic import AnyHttpUrl, BaseModel, Field

from .opportunity import OpportunityProperties
from .order import OrderParameters
from .shared import Link

type Constraints = BaseModel


class ProviderRole(StrEnum):
    licensor = "licensor"
    producer = "producer"
    processor = "processor"
    host = "host"


class Provider(BaseModel):
    name: str
    description: Optional[str] = None
    roles: list[ProviderRole]
    url: AnyHttpUrl

    # redefining init is a hack to get str type to validate for `url`,
    # as str is ultimately coerced into an AnyHttpUrl automatically anyway
    def __init__(self, url: AnyHttpUrl | str, **kwargs: Any) -> None:
        super().__init__(url=url, **kwargs)


class Product(BaseModel):
    type_: Literal["Product"] = Field(default="Product", alias="type")
    conformsTo: list[str] = Field(default_factory=list)
    id: str
    title: str = ""
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    license: str
    providers: list[Provider] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)

    # we don't want to include these in the model fields
    _constraints: type[Constraints]
    _opportunity_properties: type[OpportunityProperties]
    _order_parameters: type[OrderParameters]

    def __init__(
        self,
        *args: Any,
        constraints: type[Constraints],
        opportunity_properties: type[OpportunityProperties],
        order_parameters: type[OrderParameters],
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self._constraints = constraints
        self._opportunity_properties = opportunity_properties
        self._order_parameters = order_parameters

    @property
    def constraints(self) -> type[Constraints]:
        return self._constraints

    @property
    def opportunity_properties(self) -> type[OpportunityProperties]:
        return self._opportunity_properties

    @property
    def order_parameters(self) -> type[OrderParameters]:
        return self._order_parameters

    def with_links(self, links: list[Link] | None = None) -> Self:
        if not links:
            return self

        new = self.model_copy(deep=True)
        new.links.extend(links)
        return new


class ProductsCollection(BaseModel):
    type_: Literal["ProductCollection"] = Field(
        default="ProductCollection", alias="type"
    )
    links: list[Link] = Field(default_factory=list)
    products: list[Product]
