#!/usr/bin/env bash
set -Eeuo pipefail
# set -x # print each command before executing

for path in stapi-fastapi pystapi-validator pystapi-client stapi-pydantic; do
  name=$(basename "$path")

  set +e
  echo "Running tests for package $name"
  uv sync --package "$name"
  uv run --package "$name" --directory "$path" pytest -p no:sugar
  code=$?
  set -e

  case "$code" in
    0)   : ;;
    5)   echo "   (no tests in $name, skipping)";;
    *)   echo "   pytest failed in $name (exit $code)"; exit "$code";;
  esac
done

# finally just globally sync, so we don't just have the stapi-pydantic deps
# since this script will commonly be used before commit, and pre-commit is needed then
uv sync
