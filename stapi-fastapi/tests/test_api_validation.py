import json
import warnings
import pytest
import schemathesis
from schemathesis.checks import (
    content_type_conformance,
    negative_data_rejection,
    not_a_server_error,
    response_headers_conformance,
    response_schema_conformance,
    status_code_conformance,
)

schemathesis.experimental.OPEN_API_3_1.enable()

SCHEMA_URL = "https://raw.githubusercontent.com/stapi-spec/stapi-spec/refs/heads/main/openapi.yaml"

# Create a test schema from your ASGI app
schema = schemathesis.from_pytest_fixture("stapi_app")

@schema.parametrize()
def test_api(case):
    case.validate_response()

    not_a_server_error(case.response, case)
    status_code_conformance(case.response, case)
    content_type_conformance(case.response, case)
    response_schema_conformance(case.response, case)
    response_headers_conformance(case.response, case)
    negative_data_rejection(case.response, case)


def test_openapi_specification():
    assert schema.validate_schema


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.session.results = getattr(item.session, "results", {})
        item.session.results[item.nodeid] = rep


def pytest_sessionfinish(session, exitstatus):
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
