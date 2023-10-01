#!/bin/bash

# Build a hash for dependencies in setup.cfg and requirements-dev.txt
# just for CI caching
# this should be run any time dependencies are updated

set -o errexit -o pipefail -o nounset

install_requires="$(python <<-EOF
	from configparser import ConfigParser
	config = ConfigParser()
	config.read("setup.cfg")
	print(config["options"]["install_requires"])
EOF
)"

deps_hash="$(
    echo "$install_requires" \
    | cat requirements-dev.txt - \
    | sha256sum - \
    | awk '{print $1}'
)"

printf "# Auto generated hash from %s\n# %s\n" "$0" "$deps_hash">> requirements-dev.txt.new
grep --invert-match '^#' requirements-dev.txt >> requirements-dev.txt.new
mv requirements-dev.txt.new requirements-dev.txt
