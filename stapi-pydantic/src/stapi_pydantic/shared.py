from typing import TYPE_CHECKING, Annotated, Any, Self, TypeAlias, cast

from geojson_pydantic.types import BBox
from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from .geometry import Geometry, bbox_from_geometry_input, union_bboxes

# Shared config for the models that make up STAPI responses. Must be set on
# every model that declares an alias, not just the outermost one: model config
# is not inherited by nested models.
STAPI_RESPONSE_CONFIG = ConfigDict(
    serialize_by_alias=True,
    json_schema_serialization_defaults_required=True,
)

# As above, for response models that must also round-trip unknown fields. A dict
# literal rather than ``ConfigDict(**STAPI_RESPONSE_CONFIG, extra="allow")``,
# which type checkers reject: they cannot prove the unpacked TypedDict does not
# already carry ``extra``.
STAPI_RESPONSE_CONFIG_ALLOW_EXTRA: ConfigDict = {**STAPI_RESPONSE_CONFIG, "extra": "allow"}


#: Readable names for the type aliases the STAPI generics are parameterized
#: with. A list of pairs rather than a dict because an ``Annotated`` alias is
#: not hashable in every Python version.
_ALIAS_NAMES: list[tuple[Any, str]] = [(Geometry, "Geometry")]


def _parameter_name(parameter: Any) -> str | None:
    """A short, readable name for one generic parameter, or None if it has none.

    A class supplies its own; a type alias does not -- ``Geometry.__name__`` is
    the useless ``"Annotated"``.
    """
    for alias, name in _ALIAS_NAMES:
        if parameter is alias:
            return name
    return parameter.__name__ if isinstance(parameter, type) else None


class StapiGenericModel(BaseModel):
    """Base giving a generic STAPI model a readable parameterized name.

    Pydantic names a parameterized schema using each parameter's *repr*, which
    for the ``Geometry`` union is 150 characters of
    ``Annotated_Union_Point__MultiPoint__...``, published as a component name
    and in every ``$ref`` to it. Only the parameter spelling changes here, so
    the result is e.g. ``OpportunityCollection[Geometry, MyProperties]``.
    """

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        names = [_parameter_name(param) for param in params]
        if any(name is None for name in names):
            return super().model_parametrized_name(params)
        return f"{cls.__name__}[{', '.join(name for name in names if name is not None)}]"


def omitted_when_none(**kwargs: Any) -> Any:
    """A spec-OPTIONAL field that is omitted rather than serialized as null.

    `exclude_if` also keeps the field out of the serialization-required set
    that `json_schema_serialization_defaults_required` would otherwise put it
    in.
    """
    return Field(default=None, exclude_if=lambda v: v is None, **kwargs)


def omitted_when_empty(**kwargs: Any) -> Any:
    """A spec-OPTIONAL field that is omitted rather than serialized empty.

    For fields whose "unset" is an empty list or string rather than None.
    """
    return Field(exclude_if=lambda v: not v, **kwargs)


# A bbox the model derives from its geometry when the caller omits it. Declare
# it as ``bbox: ComputedBBox = UNSET_BBOX``.
#
# The two schema modes differ here on purpose: a caller may omit bbox, but a
# response always carries it. The ``UNSET_BBOX`` default gives the former, and
# ``json_schema_serialization_defaults_required`` the latter.
ComputedBBox: TypeAlias = BBox

# A collection bbox, derived from the members when there are any. Declare it as
# ``bbox: OptionalBBox = None``. Unlike the item bbox it is spec-OPTIONAL, and
# an empty collection has no extent, so it is absent rather than null.
OptionalBBox = Annotated[
    BBox | None,
    Field(exclude_if=lambda v: v is None),
]

#: Placeholder standing in for "derive this from the geometry". Assigned in the
#: class body rather than via ``Field(default=...)`` so the type checker also
#: treats the field as omittable: pydantic's synthesized ``__init__`` reads
#: defaults from the assignment, not from ``Annotated``.
UNSET_BBOX: BBox = cast(BBox, None)


class DerivedItemBBox(BaseModel):
    """Mixin deriving a ``ComputedBBox`` from ``geometry`` when it is omitted."""

    # Before field validation, where the geometry is still input, so ``bbox`` can
    # be declared required and non-nullable.
    @model_validator(mode="before")
    @classmethod
    def set_bbox(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("bbox") is None and data.get("geometry") is not None:
            return {**data, "bbox": bbox_from_geometry_input(data["geometry"])}
        return data


class DerivedCollectionBBox(BaseModel):
    """Mixin deriving an ``OptionalBBox`` from the members' bboxes."""

    # declared for the type checker only; the models mixing this in own the
    # real fields
    if TYPE_CHECKING:
        bbox: BBox | None
        features: list[Any]

    @model_validator(mode="after")
    def set_bbox(self) -> Self:
        # `self.features` is checked because union_bboxes returns None for an
        # empty sequence: assigning that back would re-trigger this validator
        # under validate_assignment, unbounded.
        if self.bbox is None and self.features:
            self.bbox = union_bboxes([feature.bbox for feature in self.features])
        return self


# The numberMatched collection field, under its spec alias (the field name is
# also accepted, so keyword construction still works) and omitted when unset.
NumberMatched = Annotated[
    int | None,
    Field(
        default=None,
        validation_alias=AliasChoices("numberMatched", "number_matched"),
        serialization_alias="numberMatched",
        exclude_if=lambda v: v is None,
    ),
]


class Link(BaseModel):
    href: AnyUrl
    rel: str
    type: str | None = omitted_when_none()
    title: str | None = omitted_when_none()
    method: str | None = omitted_when_none()
    headers: dict[str, str | list[str]] | None = omitted_when_none()
    body: Any = omitted_when_none()

    model_config = ConfigDict(extra="allow")

    # redefining init is a hack to get str type to validate for `href`,
    # as str is ultimately coerced into an AnyUrl automatically anyway
    # `href` must carry a default: without one, pydantic routes validation
    # through this __init__ and a payload missing `href` raises TypeError from
    # argument binding rather than yielding a ValidationError.
    def __init__(self, href: Any = None, **kwargs: Any) -> None:
        super().__init__(href=href if isinstance(href, AnyUrl) else str(href), **kwargs)
