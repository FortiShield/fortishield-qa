'''
copyright: Copyright (C) 2015-2021, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-analysisd' daemon receives the log messages and compares them to the rules.
       It then creates an alert when a log message matches an applicable rule.
       Specifically, these tests will check if the 'fortishield-analysisd' daemon correctly handles
       incoming events related to file scanning.

components:
    - analysisd

suite: scan_messages

targets:
    - manager

daemons:
    - fortishield-analysisd
    - fortishield-db

os_platform:
    - linux

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - Ubuntu Focal
    - Ubuntu Bionic

references:
    - https://fortishield.github.io/documentation/current/user-manual/reference/daemons/fortishield-analysisd.html

tags:
    - events
'''
import os

import pytest
import yaml
from fortishield_testing import global_parameters
from fortishield_testing.analysis import callback_analysisd_message, callback_fortishield_db_scan
from fortishield_testing.tools import FORTISHIELD_PATH, LOG_FILE_PATH
from fortishield_testing.tools.monitoring import ManInTheMiddle

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_path = os.path.join(test_data_path, 'scan_messages.yaml')
with open(messages_path) as f:
    test_cases = yaml.safe_load(f)

# Variables

log_monitor_paths = [LOG_FILE_PATH]
wdb_path = os.path.join(os.path.join(FORTISHIELD_PATH, 'queue', 'db', 'wdb'))
analysis_path = os.path.join(os.path.join(FORTISHIELD_PATH, 'queue', 'sockets', 'queue'))

receiver_sockets_params = [(analysis_path, 'AF_UNIX', 'UDP')]

mitm_wdb = ManInTheMiddle(address=wdb_path, family='AF_UNIX', connection_protocol='TCP')
mitm_analysisd = ManInTheMiddle(address=analysis_path, family='AF_UNIX', connection_protocol='UDP')
# monitored_sockets_params is a List of daemons to start with optional ManInTheMiddle to monitor
# List items -> (fortishield_daemon: str,(
#                mitm: ManInTheMiddle
#                daemon_first: bool))
# Example1 -> ('fortishield-clusterd', None)              Only start fortishield-clusterd with no MITM
# Example2 -> ('fortishield-clusterd', (my_mitm, True))   Start MITM and then fortishield-clusterd
monitored_sockets_params = [('fortishield-db', mitm_wdb, True), ('fortishield-analysisd', mitm_analysisd, True)]

receiver_sockets, monitored_sockets, log_monitors = None, None, None  # Set in the fixtures


# Tests

@pytest.mark.parametrize('test_case',
                         [test_case['test_case'] for test_case in test_cases],
                         ids=[test_case['name'] for test_case in test_cases])
def test_scan_messages(configure_sockets_environment, connect_to_sockets_module, wait_for_analysisd_startup,
                       test_case: list):
    '''
    description: Check if when the 'fortishield-analysisd' daemon socket receives a message with
                 a file scanning-related event, it generates the corresponding alert
                 that sends to the 'fortishield-db' daemon socket.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - configure_sockets_environment:
            type: fixture
            brief: Configure environment for sockets and MITM.
        - connect_to_sockets_module:
            type: fixture
            brief: Module scope version of 'connect_to_sockets' fixture.
        - wait_for_analysisd_startup:
            type: fixture
            brief: Wait until the 'fortishield-analysisd' has begun and the 'alerts.json' file is created.
        - test_case:
            type: list
            brief: List of tests to be performed.

    assertions:
        - Verify that the messages generated are consistent with the events received.

    input_description: Different test cases that are contained in an external YAML file (scan_messages.yaml)
                       that includes 'syscheck' events data and the expected output.

    expected_output:
        - Multiple messages (scan status logs) corresponding to each test case,
          located in the external input data file.

    tags:
        - man_in_the_middle
        - wdb_socket
    '''
    for stage in test_case:
        expected = callback_analysisd_message(stage['output'])
        receiver_sockets[0].send(stage['input'])
        response = monitored_sockets[0].start(timeout=global_parameters.default_timeout,
                                              callback=callback_fortishield_db_scan).result()
        assert response == expected, 'Failed test case stage {}: {}'.format(test_case.index(stage) + 1, stage['stage'])
