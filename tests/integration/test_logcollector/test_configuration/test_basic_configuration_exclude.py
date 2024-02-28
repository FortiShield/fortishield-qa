'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <info@fortishield.github.io>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the Fortishield component (agent or manager) starts when
       the 'exclude' tag is set in the configuration, and the Fortishield API returns the same values for
       the configured 'localfile' section.
       Log data collection is the real-time process of making sense out of the records generated by
       servers or devices. This component can receive logs through text files or Windows event logs.
       It can also directly receive logs via remote syslog which is useful for firewalls and
       other such devices.

components:
    - logcollector

suite: configuration

targets:
    - agent
    - manager

daemons:
    - fortishield-logcollector
    - fortishield-apid

os_platform:
    - linux
    - windows

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
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://documentation.fortishield.github.io/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.fortishield.github.io/current/user-manual/reference/ossec-conf/localfile.html#exclude

tags:
    - logcollector_configuration
'''
import os
import sys
from time import sleep
import pytest

from fortishield_testing import api
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.services import check_if_process_is_running, get_service


# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
no_restart_windows_after_configuration_set = True
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_basic_configuration.yaml')
logcollector_start_up_timeout = 10

fortishield.github.ioponent = get_service()

if sys.platform == 'win32':
    parameters = [
        {'LOG_FORMAT': 'syslog', 'LOCATION': r'C:\tmp\*', 'EXCLUDE': r'C:\tmp\file.txt'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': r'C:\tmp\*', 'EXCLUDE': r'C:\tmp\*.txt'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': r'C:\tmp\*', 'EXCLUDE': r'C:\tmp\file.*'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': r'C:\tmp\*', 'EXCLUDE': r'C:\tmp\file.*'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': r'C:\tmp\*', 'EXCLUDE': r'C:\tmp\file.log-%Y-%m-%d'},
    ]

    metadata = [
        {'log_format': 'syslog', 'location': r'C:\tmp\*', 'exclude': r'C:\tmp\file.txt'},
        {'log_format': 'syslog', 'location': r'C:\tmp\*', 'exclude': r'C:\tmp\*.txt'},
        {'log_format': 'syslog', 'location': r'C:\tmp\*', 'exclude': r'C:\tmp\file.*'},
        {'log_format': 'syslog', 'location': r'C:\tmp\*', 'exclude': r'C:\tmp\file.*'},
        {'log_format': 'syslog', 'location': r'C:\tmp\*', 'exclude': r'C:\tmp\file.log-%Y-%m-%d'},
    ]

else:
    parameters = [
        {'LOG_FORMAT': 'syslog', 'LOCATION': '/tmp/testing/*', 'EXCLUDE': '/tmp/testing/file.txt'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': '/tmp/testing/*', 'EXCLUDE': '/tmp/testing/f*'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': '/tmp/testing/*', 'EXCLUDE': '/tmp/testing/*g'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': '/tmp/testing/*', 'EXCLUDE': '/tmp/testing/file?.txt'},
        {'LOG_FORMAT': 'syslog', 'LOCATION': '/tmp/testing/*', 'EXCLUDE': '/tmp/testing/file.log-%Y-%m-%d'},
    ]

    metadata = [
        {'log_format': 'syslog', 'location': '/tmp/testing/*', 'exclude': '/tmp/testing/file.txt'},
        {'log_format': 'syslog', 'location': '/tmp/testing/*', 'exclude': '/tmp/testing/f*'},
        {'log_format': 'syslog', 'location': '/tmp/testing/*', 'exclude': '/tmp/testing/*g'},
        {'log_format': 'syslog', 'location': '/tmp/testing/*', 'exclude': '/tmp/testing/file?.txt'},
        {'log_format': 'syslog', 'location': '/tmp/testing/*', 'exclude': '/tmp/testing/file.log-%Y-%m-%d'},
    ]

configurations = load_fortishield_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['log_format']}_{x['location']}_{x['exclude']}" for x in metadata]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_configuration_exclude(get_configuration, configure_environment, file_monitoring, restart_logcollector):
    '''
    description: Check if the 'fortishield-logcollector' daemon starts properly when the 'exclude' tag is used.
                 For this purpose, the test will configure the logcollector to monitor a 'syslog' directory
                 and exclude log files by setting a wildcard in the 'exclude' tag. Finally, the test
                 will verify that the Fortishield component is started by checking its process, and the Fortishield API
                 returns the same values for the 'localfile' section that the configured one.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
        - restart_logcollector:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.

    assertions:
        - Verify that the Fortishield component (agent or manager) can start when the 'exclude' tag is used.
        - Verify that the Fortishield API returns the same value for the 'localfile' section as the configured one.

    input_description: A configuration template (test_basic_configuration_exclude) is contained in an external
                       YAML file (fortishield_basic_configuration.yaml). That template is combined with different
                       test cases defined in the module. Those include configuration settings for
                       the 'fortishield-logcollector' daemon.

    expected_output:
        - Boolean values to indicate the state of the Fortishield component.
    '''
    cfg = get_configuration['metadata']
    if fortishield.github.ioponent == 'fortishield-manager':
        api.wait_until_api_ready()
        api.compare_config_api_response([cfg], 'localfile')
    else:
        sleep(logcollector_start_up_timeout)

    if sys.platform == 'win32':
        assert check_if_process_is_running('fortishield-agent.exe')
    else:
        assert check_if_process_is_running('fortishield-logcollector')
