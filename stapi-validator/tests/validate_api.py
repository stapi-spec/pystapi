import schemathesis
from schemathesis.checks import (
    not_a_server_error,
    status_code_conformance,
    content_type_conformance,
    response_schema_conformance
)
import pytest
import json

schemathesis.experimental.OPEN_API_3_1.enable()

SCHEMA_URL = "https://raw.githubusercontent.com/stapi-spec/stapi-spec/refs/heads/main/openapi.yaml"
schema = schemathesis.from_uri(SCHEMA_URL)

BASE_URL = "http://localhost:8000"

@schema.parametrize()
def test_api(case):
    response = case.call_and_validate(base_url=BASE_URL)
    case.validate_response(response)
    
    not_a_server_error(response, case)
    status_code_conformance(response, case)
    content_type_conformance(response, case)
    response_schema_conformance(response, case)
    response_headers_conformance(response, case)
    negative_data_rejection(response,case)

def test_openapi_specification():
    assert schema.validate()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == 'call':
        item.session.results = getattr(item.session, 'results', {})
        item.session.results[item.nodeid] = rep

def pytest_sessionfinish(session, exitstatus):
    if hasattr(session, 'results'):
        with open('test_results.json', 'w') as f:
            json.dump({
                nodeid: {
                    'outcome': rep.outcome,
                    'longrepr': str(rep.longrepr) if rep.longrepr else None,
                }
                for nodeid, rep in session.results.items()
            }, f, indent=2)