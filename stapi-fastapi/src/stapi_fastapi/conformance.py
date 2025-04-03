from stapi_pydantic.constants import STAPI_VERSION

# API-level Conformance Classes
CORE = f"https://stapi.example.com/v{STAPI_VERSION}/core"
ORDER_STATUSES = f"https://stapi.example.com/v{STAPI_VERSION}/order-statuses"
SEARCHES_OPPORTUNITY = f"https://stapi.example.com/v{STAPI_VERSION}/searches-opportunity"
SEARCHES_OPPORTUNITY_STATUSES = f"https://stapi.example.com/v{STAPI_VERSION}/searches-opportunity-statuses"

# Product Conformance Classes
OPPORTUNITIES = f"https://stapi.example.com/v{STAPI_VERSION}/opportunities"
OPPORTUNITIES_ASYNC = f"https://stapi.example.com/v{STAPI_VERSION}/opportunities-async"
GEOJSON_POINT = "https://geojson.org/schema/Point.json"
GEOJSON_LINESTRING = "https://geojson.org/schema/Linestring.json"
GEOJSON_POLYGON = "https://geojson.org/schema/Point.json"
GEOJSON_MULTI_POINT = "https://geojson.org/schema/Point.json"
GEOJSON_MULTI_POLYGON = "https://geojson.org/schema/Point.json"
GEOJSON_MULTI_LINESTRING = "https://geojson.org/schema/Point.json"
