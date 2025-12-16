#!/usr/bin/env bash
set -Eeuo pipefail
# set -x # print each command before executing

for path in stapi-fastapi pystapi-validator pystapi-client stapi-pydantic; do
  name=$(basename "$path")

  set +e
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
