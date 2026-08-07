#!/usr/bin/env bash
set -Eeuo pipefail
# set -x # print each command before executing

# Each package carries its own `tests` package, so a single mypy invocation
# over all of them collides on the module name. Check one package at a time,
# mirroring run-tests.sh.

failed=()

for path in stapi-fastapi pystapi-validator pystapi-client stapi-pydantic; do
  name=$(basename "$path")

  set +e
  echo "Type checking package $name"
  uv run mypy "$path"
  code=$?
  set -e

  if [ "$code" -ne 0 ]; then
    failed+=("$name")
  fi
done

if [ "${#failed[@]}" -ne 0 ]; then
  echo "mypy failed in: ${failed[*]}"
  exit 1
fi
