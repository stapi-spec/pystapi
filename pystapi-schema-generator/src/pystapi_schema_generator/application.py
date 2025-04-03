from fastapi import FastAPI
from stapi_fastapi.conformance import CORE, OPPORTUNITIES
from stapi_pydantic import Product

from pystapi_schema_generator.router import RootRouter

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


def main() -> None:
    import argparse

    import yaml

    parser = argparse.ArgumentParser(description="Generate OpenAPI schema for STAPI")
    parser.add_argument(
        "--output",
        "-o",
        default="openapi.yml",
        help="Output file path for the OpenAPI schema (default: openapi.yml)",
    )
    args = parser.parse_args()

    with open(args.output, "w") as f:
        yaml.dump(app.openapi(), f)

    print(f"OpenAPI schema saved to '{args.output}'.")


if __name__ == "__main__":
    main()
