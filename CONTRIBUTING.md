# Contributing

## Getting started

Set up a virtualenv and install the project and required development
dependencies:

``` console
$ python -m venv .venv
$ pip install --editable .[dev]
```

## Linting

Lint is handled by `pre-commit`, install the git hook scripts and it should run
successfully:

``` console
$ pre-commit install
$ pre-commit run --all-files
```

## Testing

### Unit Tests

Once things are installed these should run without requiring any more setup:

``` console
$ pytest
```

### End-to-End test

These tests are found under `tests/end_to_end` and install some actual packages
and runs `py-unused-deps` on them. Once the test dependencies are installed the
tests should pass:

``` console
$ ./tests/end_to_end/data/install_all.sh
$ pytest tests/end_to_end
```
