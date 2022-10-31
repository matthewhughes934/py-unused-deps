#!/bin/bash

set -o errexit -o nounset -o pipefail

HERE="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"

find "$HERE/deps" -maxdepth 1 -mindepth 1 -type d | while read -r dep_dir
do
    cd -- "$dep_dir"
    pip install --quiet .
done

find "$HERE" -maxdepth 1 -mindepth 1 -type d -name "test_pkg_*" | while read -r pkg_dir
do
    cd -- "$pkg_dir"
    python setup.py --quiet install
    python setup.py --quiet clean --all

    if [ -e "pyproject.toml" ]
    then
        # --quiet suppresses error messages
        poetry install --all-extras
    fi
done

