#!/bin/bash

BRANCH="$1"
CONFIG_FILE_PATH="$2"
EXTRA_ARGS="${@:3}"

# Download the custom branch of fortishield-qa repository
curl -Ls https://github.com/fortishield/fortishield-qa/archive/${BRANCH}.tar.gz | tar zx &> /dev/null && mv fortishield-* fortishield-qa

# Install python dependencies not installed from
python3 -m pip install -r fortishield-qa/requirements.txt &> /dev/null

# Install Fortishield QA framework
cd fortishield-qa/deps/fortishield_testing &> /dev/null
python3 setup.py install &> /dev/null

# Run qa-ctl tool
/usr/local/bin/qa-ctl -c /fortishield_qa_ctl/${CONFIG_FILE_PATH} ${EXTRA_ARGS}
