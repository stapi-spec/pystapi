from fastapi import FastAPI
from stapi_pydantic import Product, Provider

from pystapi_schema_generator.root_router import RootRouter


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for OpenAPI spec generation."""
    app = FastAPI(
        title="STAPI API",
        description=(
            "Implementation of the STAPI specification. This API provides endpoints for discovering remote "
            "sensing data products, creating orders, and searching for acquisition opportunities across various "
            "remote sensing platforms and sensors."
        ),
        version="0.1.0",
        openapi_tags=[
            {"name": "Core", "description": "Core endpoints for API discovery and metadata"},
            {"name": "Products", "description": "Endpoints for discovering remote sensing data products"},
            {"name": "Orders", "description": "Endpoints for creating and tracking remote sensing data orders"},
            {
                "name": "Opportunities",
                "description": "Endpoints for searching remote sensing acquisition opportunities",
            },
        ],
    )

    router = RootRouter()
    router.add_product(
        Product(
            id="{productId}",
            title="A product",
            description="A product description",
            license="CC-BY-4.0",
            providers=[Provider(name="A Provider", roles=["producer"], url="https://example.com")],
            links=[],
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
