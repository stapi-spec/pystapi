from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request
from returns.result import Failure, ResultE, Success
from stapi_fastapi.models.product import Product
from stapi_fastapi.routers.product_router import ProductRouter
from stapi_pydantic import (
    Constraints,
    OpportunityProperties,
    Order,
    OrderParameters,
    OrderPayload,
    OrderProperties,
    OrderSearchParameters,
    OrderStatus,
    OrderStatusCode,
)


class StapiProductConstraints(Constraints):
    example_constraint: Any


class StapiOpportunityProperties(OpportunityProperties):
    example_property: Any


class StapiOrderParameters(OrderParameters):
    example_parameter: Any


async def stapi_create_order(
    product_router: ProductRouter, payload: OrderPayload[StapiOrderParameters], request: Request
) -> ResultE[Order[OrderStatus]]:
    """
    Create a new order.
    """
    try:
        status = OrderStatus(
            timestamp=datetime.now(UTC),
            status_code=OrderStatusCode.received,
        )
        order = Order(
            id=str(uuid4()),
            geometry=payload.geometry,
            properties=OrderProperties(
                product_id=product_router.product.id,
                created=datetime.now(UTC),
                status=status,
                search_parameters=OrderSearchParameters(
                    geometry=payload.geometry,
                    datetime=payload.datetime,
                    filter=payload.filter,
                ),
                order_parameters=payload.order_parameters.model_dump(),
                opportunity_properties={
                    "datetime": "2024-01-29T12:00:00Z/2024-01-30T12:00:00Z",
                    "off_nadir": 10,
                },
            ),
            links=[],
        )

        request.state._orders_db.put_order(order)
        request.state._orders_db.put_order_status(order.id, status)
        return Success(order)
    except Exception as e:
        return Failure(e)


example_product = Product(
    id="{productId}",
    description="An example product",
    license="CC-BY-4.0",
    links=[],
    create_order=stapi_create_order,
    search_opportunities=None,
    search_opportunities_async=None,
    get_opportunity_collection=None,
    constraints=StapiProductConstraints,
    opportunity_properties=StapiOpportunityProperties,
    order_parameters=StapiOrderParameters,
)
