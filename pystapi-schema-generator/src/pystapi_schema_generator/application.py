from fastapi import FastAPI
from stapi_fastapi.conformance import CORE, OPPORTUNITIES

from .backend import stapi_get_order, stapi_get_order_statuses, stapi_get_orders
from .product import example_product
from .router import RootRouter

router = RootRouter(
    get_orders=stapi_get_orders,
    get_order=stapi_get_order,
    get_order_statuses=stapi_get_order_statuses,
    get_opportunity_search_records=None,
    get_opportunity_search_record=None,
    conformances=[CORE, OPPORTUNITIES],
)
router.add_product(example_product)

app: FastAPI = FastAPI(
    openapi_tags=[
        {
            "name": "Core",
            "description": "Core endpoints",
        },
        {
            "name": "Orders",
            "description": "Endpoint for creating and managing orders",
        },
        {
            "name": "Opportunities",
            "description": "Endpoint for viewing and accepting opportunities",
        },
        {
            "name": "Products",
            "description": "Products",
        },
    ]
)
app.include_router(router, prefix="")
