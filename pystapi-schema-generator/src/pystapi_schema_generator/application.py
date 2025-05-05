from fastapi import FastAPI
from stapi_pydantic import Product, Provider

from pystapi_schema_generator import STAPI_BASE_URL, STAPI_VERSION
from pystapi_schema_generator.root_router import RootRouter


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for OpenAPI spec generation."""
    app = FastAPI(
        title="STAPI API",
        description=(
            "Implementation of the STAPI specification. This API provides endpoints for discovering remote "
            "sensing data products, creating orders, and searching for acquisition opportunities across various "
            "remote sensing platforms and sensors. The API follows the STAPI specification for standardized "
            "interaction with remote sensing data providers."
        ),
        version=STAPI_VERSION,
        openapi_tags=[
            {
                "name": "Core",
                "description": (
                    "Core endpoints for API discovery and metadata. These endpoints provide "
                    "essential information about the API's capabilities and available resources."
                ),
                "externalDocs": {
                    "description": "STAPI Core Specification",
                    "url": "https://github.com/stapi-spec/stapi-spec/blob/main/core/README.md",
                },
            },
            {
                "name": "Products",
                "description": (
                    "Endpoints for discovering and accessing remote sensing data products. "
                    "Each product endpoint provides detailed metadata, queryable properties, "
                    "and order parameters specific to that product."
                ),
                "externalDocs": {
                    "description": "STAPI Product Specification",
                    "url": "https://github.com/stapi-spec/stapi-spec/blob/main/product/README.md",
                },
            },
            {
                "name": "Orders",
                "description": (
                    "Endpoints for creating and managing remote sensing data orders. "
                    "Supports order creation, status tracking, and delivery management "
                    "with comprehensive state machine implementation."
                ),
                "externalDocs": {
                    "description": "STAPI Order Specification",
                    "url": "https://github.com/stapi-spec/stapi-spec/blob/main/order/README.md",
                },
            },
            {
                "name": "Opportunities",
                "description": (
                    "Endpoints for searching remote sensing acquisition opportunities. "
                    "Supports both synchronous and asynchronous search modes with "
                    "spatial, temporal, and property-based filtering."
                ),
                "externalDocs": {
                    "description": "STAPI Opportunity Specification",
                    "url": "https://github.com/stapi-spec/stapi-spec/blob/main/opportunity/README.md",
                },
            },
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    router = RootRouter()
    router.add_product(
        Product(
            id="{productId}",
            title="Example Product",
            description=(
                "This is an example product that demonstrates the STAPI specification. "
                "Implementers should replace this with their actual product definitions, "
                "including specific metadata, queryable properties, and order parameters."
            ),
            license="proprietary",
            providers=[
                Provider(
                    name="Example Provider",
                    roles=["producer"],
                    url="https://example.com/provider",
                    description="Example provider for demonstration purposes",
                )
            ],
            links=[],
            stapi_type="Product",
            stapi_version=STAPI_VERSION,
            conformsTo=[
                f"{STAPI_BASE_URL}/{STAPI_VERSION}/core",
                "https://geojson.org/schema/Polygon.json",
            ],
        )
    )

    app.include_router(router, prefix="")

    return app


# Create the FastAPI application instance
app = create_app()


def main() -> None:
    """Generate OpenAPI schema for STAPI."""
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
