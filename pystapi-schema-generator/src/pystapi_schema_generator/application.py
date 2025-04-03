from fastapi import FastAPI
from stapi_fastapi.conformance import CORE, OPPORTUNITIES
from stapi_pydantic import Product

from .router import RootRouter

router = RootRouter(conformances=[CORE, OPPORTUNITIES])


router.add_product(
    Product(
        id="{productId}",
        description="An example product",
        license="CC-BY-4.0",
        links=[],
    )
)

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
