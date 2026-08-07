"""Path parameter annotations.

Aliased so the published names stay camelCase, as the spec documents them,
while the Python parameters stay snake_case.
"""

from typing import Annotated

from fastapi import Path

# Titles are explicit because FastAPI would otherwise derive them from the
# alias, yielding "Orderid" rather than "Order ID".
OrderIdPath = Annotated[str, Path(alias="orderId", title="Order ID")]
SearchRecordIdPath = Annotated[str, Path(alias="searchRecordId", title="Search Record ID")]
OpportunityCollectionIdPath = Annotated[str, Path(alias="opportunityCollectionId", title="Opportunity Collection ID")]
