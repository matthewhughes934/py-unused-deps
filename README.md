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

    usage: py-unused-deps [-h] [-d DISTRIBUTION] [-v] [-i IGNORE] [-e EXTRAS] [-r REQUIREMENTS] [--include INCLUDE] [--exclude EXCLUDE]
                          [--config-file CONFIG_FILE]
                          [filepaths ...]
    
    positional arguments:
      filepaths             Paths to scan for dependency usage
    
    options:
      -h, --help            show this help message and exit
      -d DISTRIBUTION, --distribution DISTRIBUTION
                            The distribution to scan for unused dependencies
      -v, --verbose
      -i IGNORE, --ignore IGNORE
                            Dependencies to ignore when scanning for usage. For example, you might want to ignore a linter that you run but don't import
      -e EXTRAS, --extra EXTRAS
                            Extra environment to consider when loading dependencies
      -r REQUIREMENTS, --requirement REQUIREMENTS
                            File listing extra requirements to scan for
      --include INCLUDE     Pattern to match on files when measuring usage
      --exclude EXCLUDE     Pattern to match on files or directory to exclude when measuring usage
      --config-file CONFIG_FILE
                            File to load config from

### File Discovery

The positional `filepaths` provides the location to search for files. Files
under this path are matched according to the `--include` argument. This can be
given multiple times and arguments are used interpreted as wildcard patterns
(specifically, they are parsed to
[`fnmatch.fnmatch`](https://docs.python.org/3/library/fnmatch.html#fnmatch.fnmatch).
The default is to include files that match against `*.py` or `*.pyi`.

Files can be excluded with the `--exclude` flag, which can also be given
multiple times. Similarly to `--include` these are interpreted as shell wildcard
patterns, with the addition that:

  - Patterns are matched against entire directory names, so `__pycache__` will
    exclude any directory containing `__pycache__`
  - Patterns are expanded using
    [`os.path.abspath`](https://docs.python.org/3/library/os.path.html#os.path.abspath)

The default list of exclude patterns is: `.svn`, `CVS`, `.bzr`, `.hg`, `.git`,
`__pycache__`, `.tox`, `.nox`, `.eggs`, `*.egg`, `.venv`, `venv`,

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

### Configuration from file

By default, configuration will be searched for in `pyproject.toml` under the key
`tool.py-unused-deps`:

``` toml
# pyproject.toml example
[tool.py-unused-deps]
verbose = 1
```

Otherwise, configuration may be stored in any TOML file under the key
`py-unused-deps`, this file can then be passed via the `--configuration-file`
argument.

``` toml
# non pyproject.toml example
[py-unused-deps]
verbose = 1
```

The types of configuration variables and how they map to the flags:

  - `filepaths`: array of strings
  - `distribution` (`-d/--distribution`): string
  - `ignore` (`-i/--ignore`): array of strings
  - `extras` (`-e/--extra`): array of strings
  - `requirements` (`-r/--requirement`): array of strings
  - `include` (`-i/--include`): array of strings
  - `exclude` (`-i/--exclude`): array of strings
  - `verbose` (`-v/--verbose`): integer
