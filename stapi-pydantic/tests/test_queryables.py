from stapi_pydantic import Queryables


class ParentQueryables(Queryables):
    pass


class ChildQueryables(ParentQueryables):
    gsd: float


class UnrelatedQueryables(Queryables):
    platform: str


def test_required_property_names_is_isolated_per_class() -> None:
    # the cache keys on cls, so no class ever reads another's result --
    # including a parent's, which a plain class attribute would inherit
    assert ChildQueryables.required_property_names() == frozenset({"gsd"})
    assert ParentQueryables.required_property_names() == frozenset()
    assert UnrelatedQueryables.required_property_names() == frozenset({"platform"})
    assert Queryables.required_property_names() == frozenset()


def test_required_property_names_is_cached() -> None:
    assert ChildQueryables.required_property_names() is ChildQueryables.required_property_names()


def test_required_property_names_omits_optional_queryables() -> None:
    class Optional_(Queryables):
        gsd: float | None = None

    assert Optional_.required_property_names() == frozenset()
