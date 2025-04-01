from stapi_pydantic import Product


def test_model_validate() -> None:
    Product.model_validate(
        {
            "type": "Product",
            "id": "an-id",
            "description": "A description",
            "license": "other",
            "links": [],
        }
    )
