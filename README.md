# py-unused-deps

Find unused dependencies in your Python projects.

This application works by inspecting the metadata of your distribution and its
dependencies. This means the current project **must be installed** and
`py-unused-deps` must be run from within the same environment as the project,
and its dependencies, are installed within. For example using `setuptools`:

``` console
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install --editable .
$ pip install unused-deps
$ py-unused-deps
```

## Usage

    usage: py-unused-deps [-h] [-d DISTRIBUTION] [-v] [-i IGNORE] [-s SOURCE] [-e EXTRA]
    
    options:
      -h, --help            show this help message and exit
      -d DISTRIBUTION, --distribution DISTRIBUTION
                            The distribution to scan for unused dependencies
      -v, --verbose
      -i IGNORE, --ignore IGNORE
                            Dependencies to ignore when scanning for usage. For example, you might want to ignore a linter that you run but don't import
      -s SOURCE, --source SOURCE
                            Extra directories to scan for python files to check for dependency usage
      -e EXTRA, --extra EXTRA
                            Extra environment to consider when loading dependencies

### Distribution detection

By default `py-unused-deps` will scan any `pyproject.toml` or
`setup.cfg/setup.py` file to try and detect a distribution. This may not always
be accurate, so you can specify a distribution to scan with `--distribution`

### Extra dependencies

You distribution may contain extra optional dependencies to be installed like
`pip install --editable .[tests]`. To also scan these you can use the `--extra`
flag. This can be used multiple times:

``` console
$ pip install --editable .[tests,security]
$ py-unuse-deps --extra tests --extra security
```
