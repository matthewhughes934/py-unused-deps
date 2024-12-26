# Contributing

## Getting started

Dependencies are managed with [`pipenv`](https://pipenv.pypa.io/en/latest/), a
quick setup looks something like:

``` console
$ pipenv install --dev
# run everything from within a virtualenv
$ source "$(pipenv --venv)/bin/activate"
# alternatively, spawn a shell
$ pipenv shell
```

## Linting

Linting is handled by `pre-commit`, install the git hook scripts and it should
run successfully:

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
$ ./tests/end_to_end/data/install_all.py
$ pytest tests/end_to_end
```
