#!/bin/bash

# Build a hash for dependencies in setup.cfg and requirements-dev.txt
# just for CI caching
# this should be run any time dependencies are updated

set -o errexit -o pipefail -o nounset

install_requires="$(python -c '\
    from configparser import ConfigParser; \
    config = ConfigParser(); \
    config.read("setup.cfg"); \
    print(config["options"]["install_requires"]) \
')"

deps_hash="$(
    echo "$install_requires" \
    | cat requirements-dev.txt - \
    | sha256sum - \
    | awk '{print $1}'
)"

printf "# Auto generated hash from $0\n# $deps_hash\n" >> requirements-dev.txt.new
cat requirements-dev.txt >> requirements-dev.txt.new
mv requirements-dev.txt.new requirements-dev.txt
