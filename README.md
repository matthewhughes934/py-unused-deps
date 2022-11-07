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

    usage: py-unused-deps [-h] [-d DISTRIBUTION] [-v] [-i IGNORE] [-s SOURCE] [-e EXTRA] [-r REQUIREMENT]

    options:
      -h, --help            show this help message and exit
      -d DISTRIBUTION, --distribution DISTRIBUTION
                            The distribution to scan for unused dependencies
      -v, --verbose
      -i IGNORE, --ignore IGNORE
                            Dependencies to ignore when scanning for usage. For example, you might want to ignore a linter that you run but
                            don't import
      -s SOURCE, --source SOURCE
                            Extra directories to scan for python files to check for dependency usage
      -e EXTRA, --extra EXTRA
                            Extra environment to consider when loading dependencies
      -r REQUIREMENT, --requirement REQUIREMENT
                            File listing extra requirements to scan for

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
$ py-unused-deps --extra tests --extra security
```

### Requirements File

Similar to above, you may have a distribution with some dev-only dependencies
that you want to ensure you're using, e.g. for tests. If these dependencies are
in a file you can include them with the `--requirement` flag:

``` console
$ pip install --editable .
$ pip install --requirement requirements-tests.txt
$ py-unused-deps --requirement requirements-test.txt
```

Note: this flag does not support the full requirements spec [as defined by
pip](https://pip.pypa.io/en/stable/reference/requirements-file-format/) but just
comments and requirement specifications.

For example, each of the following requirements would be included:

    pytest
    pytest-cov
    beautifulsoup4
    docopt == 0.6.1
    requests [security] >= 2.8.1, == 2.8.* ; python_version < "2.7"
    urllib3 @ https://github.com/urllib3/urllib3/archive/refs/tags/1.26.8.zip

But all of the following would be skipped:

    # unsupported: pip specific flags
    -r other-requirements.txt
    -c constraints.txt
    
    # unsupported: paths
    ./downloads/numpy-1.9.2-cp34-none-win32.whl
    
    # unsupported: plain URL
    http://wxpython.org/Phoenix/snapshot-builds/wxPython_Phoenix-3.0.3.dev1820+49a8884-cp34-none-win_amd64.whl
