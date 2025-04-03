from fastapi import FastAPI
from stapi_fastapi.conformance import CORE, OPPORTUNITIES

from .product import example_product
from .router import RootRouter

router = RootRouter(conformances=[CORE, OPPORTUNITIES])
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
