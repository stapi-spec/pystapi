import json
import os
from collections.abc import Generator
from typing import Protocol, cast

import pluggy
import pytest
import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.checks import not_a_server_error

# The OpenAPI-specific checks are only re-exported by schemathesis.checks;
# import them from the module that defines them.
from schemathesis.specs.openapi.checks import (
    content_type_conformance,
    negative_data_rejection,
    response_headers_conformance,
    response_schema_conformance,
    status_code_conformance,
)

schemathesis.experimental.OPEN_API_3_1.enable()

# The document to validate against, supplied by the caller rather than exported
# from the application under test.
#
# These tests drive a live server, so they are opt-in; skipping at module level
# keeps them out of the ordinary unit-test run without pretending they passed.
SCHEMA_PATH = os.environ.get("STAPI_OPENAPI_SCHEMA")
if SCHEMA_PATH is None:
    pytest.skip(
        "set STAPI_OPENAPI_SCHEMA and run a server, or use the pystapi-validator CLI",
        allow_module_level=True,
    )

schema = schemathesis.from_path(SCHEMA_PATH)

BASE_URL = os.environ.get("STAPI_BASE_URL", "http://localhost:8000")


# Hypothesis filters out every candidate it generates for the POST bodies. That
# is a limitation of the generator, not a server/spec disagreement, so it must
# not mask the contract checks below.
@settings(suppress_health_check=[HealthCheck.filter_too_much])
@schema.parametrize()
def test_api(case: schemathesis.Case) -> None:
    # Checks take a CheckContext that only schemathesis can build, so hand them
    # to call_and_validate rather than invoking them directly.
    case.call_and_validate(
        base_url=BASE_URL,
        checks=(
            not_a_server_error,
            status_code_conformance,
            content_type_conformance,
            response_schema_conformance,
            response_headers_conformance,
            negative_data_rejection,
        ),
    )


def test_openapi_specification() -> None:
    # Raises on an invalid schema; there is no return value to assert on.
    schema.validate()


class _ResultsSession(Protocol):
    """Structural view of the session with the ``results`` attribute these hooks attach to it."""

    results: dict[str, pytest.TestReport]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pluggy.Result[pytest.TestReport], None]:
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        session = cast(_ResultsSession, item.session)
        session.results = getattr(item.session, "results", {})
        session.results[item.nodeid] = rep


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if hasattr(session, "results"):
        with open("test_results.json", "w") as f:
            json.dump(
                {
                    nodeid: {
                        "outcome": rep.outcome,
                        "longrepr": str(rep.longrepr) if rep.longrepr else None,
                    }
                    for nodeid, rep in session.results.items()
                },
                f,
                indent=2,
            )
