'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-analysisd' daemon receives the log messages and compares them to the rules.
       It then creates an alert when a log message matches an applicable rule.
       Specifically, these tests will verify if the 'fortishield-analysisd' daemon generates valid
       alerts from Windows registry-related 'syscheck' events.

components:
    - analysisd

suite: all_syscheckd_configurations

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
from fortishield_testing.analysis import validate_analysis_alert_complex
from fortishield_testing.tools import FORTISHIELD_PATH, LOG_FILE_PATH, ALERT_FILE_PATH
from fortishield_testing.tools.monitoring import ManInTheMiddle

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=2), pytest.mark.server]

# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_path = os.path.join(test_data_path, 'syscheck_registry_events_win32.yaml')

with open(messages_path) as f:
    test_cases = yaml.safe_load(f)

# Variables

log_monitor_paths = [LOG_FILE_PATH, ALERT_FILE_PATH]
analysis_path = os.path.join(os.path.join(FORTISHIELD_PATH, 'queue', 'sockets', 'queue'))

receiver_sockets_params = [(analysis_path, 'AF_UNIX', 'UDP')]

mitm_analysisd = ManInTheMiddle(address=analysis_path, family='AF_UNIX', connection_protocol='UDP')
# monitored_sockets_params is a List of daemons to start with optional ManInTheMiddle to monitor
# List items -> (fortishield_daemon: str,(
#                mitm: ManInTheMiddle
#                daemon_first: bool))
# Example1 -> ('fortishield-clusterd', None)              Only start fortishield-clusterd with no MITM
# Example2 -> ('fortishield-clusterd', (my_mitm, True))   Start MITM and then fortishield-clusterd
monitored_sockets_params = [('fortishield-db', None, None), ('fortishield-analysisd', mitm_analysisd, True)]

receiver_sockets, monitored_sockets, log_monitors = None, None, None  # Set in the fixtures

events_dict = {}
alerts_list = []
analysisd_injections_per_second = 200


# Fixtures


@pytest.fixture(scope='module', params=range(len(test_cases)))
def get_alert(request):
    return alerts_list[request.param]


def test_validate_all_win32_registry_alerts(configure_sockets_environment, connect_to_sockets_module,
                                            wait_for_analysisd_startup, generate_events_and_alerts, get_alert):
    '''
    description: Check if the alerts generated by the 'fortishield-analysisd' daemon from Windows registry-related
                 'syscheck' events are valid. The 'validate_analysis_alert_complex' function checks if
                 an 'analysisd' alert is properly formatted in reference to its 'syscheck' event.

    fortishield_min_version: 4.2.0

    tier: 2

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
        - generate_events_and_alerts:
            type: fixture
            brief: Read the specified YAML and generate every event and alert using the input from every test case.
        - get_alert:
            type: fixture
            brief: List of alerts to be validated.

    assertions:
        - Verify that the alerts generated are consistent with the events received.

    input_description: Different test cases that are contained in an external
                       YAML file (syscheck_registry_events_win32.yaml)
                       that includes 'syscheck' events data and the expected output.

    inputs:
        - 20254 test cases distributed among 'syscheck' events of type 'added', 'modified', and 'deleted'.

    expected_output:
        - Multiple messages (alert logs) corresponding to each test case,
          located in the external input data file.

    tags:
        - alerts
        - man_in_the_middle
        - wdb_socket
    '''
    alert = get_alert
    path = alert['syscheck']['path']
    mode = alert['syscheck']['event'].title()

    try:
        value_name = alert['syscheck']['value_name']
        path += '\\' + value_name
    except KeyError:
        pass

    validate_analysis_alert_complex(alert, events_dict[path][mode], schema='win32')
