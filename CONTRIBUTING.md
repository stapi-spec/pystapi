# Contributing

First, thanks for contributing to **pystapi**!
The [README](./README.md#development) as instructions on setting up your development environment, which is a great place to start.

## Repository organization

**pystapi** is a "monorepo", meaning that it contains several sub-projects.
Each project has it's own `pyproject.toml` file, README, CHANGELOG, tests, and more.
Development dependencies should be specified at the top-level `pyproject.toml` file, as tests are intended to be run for the entire repository at once.

## Branches

We have a single primary development branch, **main**.
Releases are cut from this branch by tags.
Tags are named to identify which project they are releasing, e.g. a **stapi-pydantic** tag might look like `stapi-pydantic/v0.1.2`.
If necessary, long-lived release branches are used to manage non-breaking changes and fixes, e.g. a `stapi-pydantic/v0.1` branch to handle any bugfixes that need to be backported to the v0.1 lineage of the project after **main** has incorporated breaking changes.

## Testing

We use [pytest](https://docs.pytest.org).
Tests should be written in the "pytest style", i.e. free functions.

Good:

```python
def test_foo() -> None:
    assert 1 == 1
```

Bad:

```python
class FooTest(unittest.TestCase):
    def test_foo(self) -> None:
        assert 1 == 1
```

## Static typing

We use [mypy](https://mypy-lang.org/) for static typing.
When possible, projects work in `strict` mode, meaning that type checking is strongly enforced.
Some projects are not quite ready for `strict` mode, but we want to get them there.

## Docs

We use [mkdocs](https://www.mkdocs.org/) for our [documentation](/docs/).
To build the docs, run `uv run mkdocs build`.
To serve the docs locally, run `uv run mkdocs serve`.

## Lints and checks

We use [pre-commit](https://pre-commit.com/).
If you want to run checks on every commit:

```shell
uv run pre-commit install
```

If you ever need to disable **pre-commit** when committing use `--no-verify`:

```shell
git commit --no-verify
```

## Submitting changes

Open a [pull request](https://github.com/stapi-spec/pystapi/pulls) with your changes, and fill out the provided template.
It's not required, but it's helpful if you name your pull request in the [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/) style, as the pull request titles are the eventual commit title for your changes (we use squash-and-merge).
A **pystapi** maintainer will review your PR and request any changes.
Once approved, if you have the permissions you can merge your PR ... if you don't, a maintainer will.

If your PR is not ready for review, but you'd like some feedback on it anyways, open it as a draft.
