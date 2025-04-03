# TODO make these typed dicts to get type hints

from stapi_pydantic.constants import STAPI_VERSION

API = {
    "core": f"https://stapi.example.com/v{STAPI_VERSION}/core",
    "order-statuses": f"https://stapi.example.com/v{STAPI_VERSION}/order-statuses",
    "searches-opportunity": f"https://stapi.example.com/v{STAPI_VERSION}/searches-opportunity",
    "searches-opportunity-statuses": f"https://stapi.example.com/v{STAPI_VERSION}/searches-opportunity-statuses",
}

PRODUCT = {
    "opportunities": f"https://stapi.example.com/v{STAPI_VERSION}/opportunities",
    "opportunities-async": f"https://stapi.example.com/v{STAPI_VERSION}/opportunities-async",
    "geojson-point": "https://geojson.org/schema/Point.json",
    "geojson-linestring": "https://geojson.org/schema/LineString.json",
    "geojson-polygon": "https://geojson.org/schema/Polygon.json",
    "geojson-multi-point": "https://geojson.org/schema/MultiPoint.json",
    "geojson-multi-polygon": "https://geojson.org/schema/MultiPolygon.json",
    "geojson-multi-linestring": "https://geojson.org/schema/MultiLineString.json",
}
