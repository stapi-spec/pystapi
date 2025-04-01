from stapi_pydantic import OpportunityProperties


def test_create_properties() -> None:
    _ = OpportunityProperties.model_validate(
        {"datetime": "2025-04-01T00:00:00Z/2025-04-01T23:59:59Z", "product_id": "foo"}
    )
