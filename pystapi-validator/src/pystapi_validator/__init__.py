import argparse
import os
import sys
from pathlib import Path

import pytest

#: The schemathesis suite this CLI drives, resolved from this file so the CLI
#: does not depend on the working directory.
TESTS = Path(__file__).resolve().parents[2] / "tests"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a running STAPI server against an OpenAPI document.",
    )
    parser.add_argument("schema", help="path to the OpenAPI document to validate against")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="base URL of the running server (default: %(default)s)",
    )
    args = parser.parse_args()

    if not Path(args.schema).is_file():
        parser.error(f"no such document: {args.schema}")
    if not TESTS.is_dir():
        parser.error(f"test suite not found at {TESTS}; run from a source checkout")

    # read by the suite at import time; unset, it would skip every check and
    # still exit 0
    os.environ["STAPI_OPENAPI_SCHEMA"] = args.schema
    os.environ["STAPI_BASE_URL"] = args.base_url

    sys.exit(pytest.main([str(TESTS), "-q"]))


if __name__ == "__main__":
    main()
