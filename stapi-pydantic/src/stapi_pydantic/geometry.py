from collections.abc import Sequence
from typing import Annotated, Any, TypeAlias

from geojson_pydantic.geometries import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from geojson_pydantic.types import BBox
from pydantic import Field, TypeAdapter

#: The geometry types STAPI defines, discriminated on ``type``.
#:
#: Deliberately narrower than ``geojson_pydantic.Geometry``: there is no
#: conformance class for ``GeometryCollection``, so no implementation could
#: declare support for one.
Geometry: TypeAlias = Annotated[
    Point | MultiPoint | LineString | MultiLineString | Polygon | MultiPolygon,
    Field(discriminator="type"),
]

_GEOMETRY_ADAPTER: TypeAdapter[Geometry] = TypeAdapter(Geometry)


def _all_coordinates(geometry: Geometry) -> list[list[float]]:
    """Flatten a GeoJSON geometry's coordinates to a list of positions."""

    def flatten(coords: Any) -> list[list[float]]:
        if coords and isinstance(coords[0], int | float):
            return [list(coords)]
        return [p for c in coords for p in flatten(c)]

    return flatten(geometry.coordinates)


def compute_geometry_bbox(geometry: Geometry) -> BBox:
    """Compute an RFC 7946 bbox (2D or 3D) from a geometry's coordinates."""
    coords = _all_coordinates(geometry)
    if not coords:
        raise ValueError("cannot compute bbox: geometry has no coordinates")
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    # a third position element is always elevation, never a measure (RFC 7946 3.1.1)
    if all(len(c) == 3 for c in coords):
        elevations = [c[2] for c in coords]
        return (min(lons), min(lats), min(elevations), max(lons), max(lats), max(elevations))
    return (min(lons), min(lats), max(lons), max(lats))


def bbox_from_geometry_input(geometry: Any) -> BBox:
    """Compute a bbox from a geometry in model, mapping, or ``__geo_interface__``
    form.
    """
    if hasattr(geometry, "__geo_interface__"):
        geometry = geometry.__geo_interface__
    return compute_geometry_bbox(_GEOMETRY_ADAPTER.validate_python(geometry))


def union_bboxes(bboxes: Sequence[BBox]) -> BBox | None:
    """Union RFC 7946 bboxes into one, or None if there are none to union.

    The result is 3D only when every input is 3D; a mix degrades to 2D since
    elevation is unknown for the 2D members.
    """
    values = [list(b) for b in bboxes]
    if not values:
        return None
    if all(len(v) == 6 for v in values):
        return (
            min(v[0] for v in values),
            min(v[1] for v in values),
            min(v[2] for v in values),
            max(v[3] for v in values),
            max(v[4] for v in values),
            max(v[5] for v in values),
        )
    horizontals = [(v[0], v[1], v[3], v[4]) if len(v) == 6 else (v[0], v[1], v[2], v[3]) for v in values]
    return (
        min(h[0] for h in horizontals),
        min(h[1] for h in horizontals),
        max(h[2] for h in horizontals),
        max(h[3] for h in horizontals),
    )
