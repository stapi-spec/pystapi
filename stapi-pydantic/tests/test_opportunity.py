from stapi_pydantic import Opportunity


def test_model_validate() -> None:
    Opportunity.model_validate(
        {
            "type": "Feature",
            "geometry": None,
            "properties": {
                "datetime": "2025-03-25T00:00:00Z/..",
                "product_id": "an-id",
            },
        }
    )
