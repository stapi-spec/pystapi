from __future__ import annotations

from typing import TYPE_CHECKING, Any

from stapi_pydantic import OpportunityProperties, OrderParameters, Queryables
from stapi_pydantic import Product as BaseProduct

if TYPE_CHECKING:
    from stapi_fastapi.backends.product_backend import (
        CreateOrder,
        GetOpportunityCollection,
        SearchOpportunities,
        SearchOpportunitiesAsync,
    )


class Product(BaseProduct):
    _create_order: CreateOrder
    _search_opportunities: SearchOpportunities | None
    _search_opportunities_async: SearchOpportunitiesAsync | None
    _get_opportunity_collection: GetOpportunityCollection | None

    # we don't want to include these in the model fields
    _queryables: type[Queryables]
    _opportunity_properties: type[OpportunityProperties]
    _order_parameters: type[OrderParameters]

    def __init__(
        self,
        *args: Any,
        create_order: CreateOrder,
        search_opportunities: SearchOpportunities | None = None,
        search_opportunities_async: SearchOpportunitiesAsync | None = None,
        get_opportunity_collection: GetOpportunityCollection | None = None,
        queryables: type[Queryables],
        opportunity_properties: type[OpportunityProperties],
        order_parameters: type[OrderParameters],
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        if bool(search_opportunities_async) != bool(get_opportunity_collection):
            raise ValueError(
                "Both the `search_opportunities_async` and `get_opportunity_collection` "
                "arguments must be provided if either is provided"
            )

        self._create_order = create_order
        self._search_opportunities = search_opportunities
        self._search_opportunities_async = search_opportunities_async
        self._get_opportunity_collection = get_opportunity_collection
        self._queryables = queryables
        self._opportunity_properties = opportunity_properties
        self._order_parameters = order_parameters

    @property
    def create_order(self) -> CreateOrder:
        return self._create_order

    @property
    def search_opportunities(self) -> SearchOpportunities:
        if not self._search_opportunities:
            raise AttributeError("This product does not support opportunity search")
        return self._search_opportunities

    @property
    def search_opportunities_async(self) -> SearchOpportunitiesAsync:
        if not self._search_opportunities_async:
            raise AttributeError("This product does not support async opportunity search")
        return self._search_opportunities_async

    @property
    def get_opportunity_collection(self) -> GetOpportunityCollection:
        if not self._get_opportunity_collection:
            raise AttributeError("This product does not support async opportunity search")
        return self._get_opportunity_collection

    @property
    def supports_opportunity_search(self) -> bool:
        return self._search_opportunities is not None

    @property
    def supports_async_opportunity_search(self) -> bool:
        return self._search_opportunities_async is not None and self._get_opportunity_collection is not None

    @property
    def queryables(self) -> type[Queryables]:
        return self._queryables

    @property
    def opportunity_properties(self) -> type[OpportunityProperties]:
        return self._opportunity_properties

    @property
    def order_parameters(self) -> type[OrderParameters]:
        return self._order_parameters
