# This is some slightly strange magic to get "static" structures with
# attributes, to make it pleasant to use in an editor with autocompletion.

import dataclasses
from dataclasses import dataclass

from stapi_pydantic.constants import STAPI_VERSION


@dataclass(frozen=True)
class _All:
    def all(self) -> list[str]:
        return [getattr(self, field.name) for field in dataclasses.fields(self)]


@dataclass(frozen=True)
class _Api(_All):
    core: str = f"https://stapi.example.com/v{STAPI_VERSION}/core"
    order_statuses: str = f"https://stapi.example.com/v{STAPI_VERSION}/order-statuses"
    searches_opportunity: str = f"https://stapi.example.com/v{STAPI_VERSION}/searches-opportunity"
    searches_opportunity_statuses: str = f"https://stapi.example.com/v{STAPI_VERSION}/searches-opportunity-statuses"


@dataclass(frozen=True)
class _Product(_All):
    opportunities: str = f"https://stapi.example.com/v{STAPI_VERSION}/opportunities"
    opportunities_async: str = f"https://stapi.example.com/v{STAPI_VERSION}/opportunities-async"
    geojson_point: str = "https://geojson.org/schema/Point.json"
    geojson_linestring: str = "https://geojson.org/schema/LineString.json"
    geojson_polygon: str = "https://geojson.org/schema/Polygon.json"
    geojson_multi_point: str = "https://geojson.org/schema/MultiPoint.json"
    geojson_multi_polygon: str = "https://geojson.org/schema/MultiPolygon.json"
    geojson_multi_linestring: str = "https://geojson.org/schema/MultiLineString.json"


API = _Api()
"""API (top level) conformances"""

PRODUCT = _Product()
"""Product conformances"""
