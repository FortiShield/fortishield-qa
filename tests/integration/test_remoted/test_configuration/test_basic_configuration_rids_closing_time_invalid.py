'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.
           Created by Fortishield, Inc. <info@fortishield.github.io>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-remoted' program is the server side daemon that communicates with the agents.
       Specifically, this test will check if 'fortishield-remoted' produces an error message when an
       invalid 'rids_closing_time' value is set.

components:
    - remoted

suite: configuration

targets:
    - manager

daemons:
    - fortishield-remoted

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
    - https://documentation.fortishield.github.io/current/user-manual/reference/daemons/fortishield-remoted.html
    - https://documentation.fortishield.github.io/current/user-manual/reference/ossec-conf/remote.html
    - https://documentation.fortishield.github.io/current/user-manual/agents/agent-life-cycle.html
    - https://documentation.fortishield.github.io/current/user-manual/capabilities/agent-key-polling.html

tags:
    - remoted
'''
import os
import pytest

from fortishield_testing.generic_callbacks import callback_error_invalid_value_for
from fortishield_testing.tools.monitoring import REMOTED_DETECTOR_PREFIX
from fortishield_testing.tools.configuration import load_fortishield_configurations

# Marks
pytestmark = [pytest.mark.server, pytest.mark.tier(level=0)]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_basic_configuration.yaml')

parameters = [
    {'CONNECTION': 'secure', 'PORT': '1514', 'RIDS_CLOSING_TIME': '0s'},
    {'CONNECTION': 'secure', 'PORT': '1514', 'RIDS_CLOSING_TIME': '4S'}
]

metadata = [
    {'connection': 'secure', 'port': '1514', 'rids_closing_time': '0'},
    {'connection': 'secure', 'port': '1514', 'rids_closing_time': '4S'}
]

configurations = load_fortishield_configurations(configurations_path, "test_basic_configuration_rids_closing_time",
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['CONNECTION'], x['PORT'], x['RIDS_CLOSING_TIME']}" for x in parameters]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_rids_closing_time_invalid(get_configuration, configure_environment, restart_remoted):
    '''
    description: Check if 'fortishield-remoted' fails when an invalid 'rids_closing_time' value is set. For this purpose, 
                 it uses the configuration from test cases and check if the warning has been logged.
    
    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing. Restart Fortishield is needed for applying the configuration.
        - restart_remoted:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.
    
    assertions:
        - Verify that remoted starts correctly.
        - Verify that the warning is logged correctly in ossec.log.
    
    input_description: A configuration template (test_basic_configuration_rids_closing_time) is contained in an external
                       YAML file, (fortishield_basic_configuration.yaml). That template is combined with different test cases
                       defined in the module. Those include configuration settings for the 'fortishield-remoted' daemon and
                       agents info.
    
    expected_output:
        - r'Started <pid>: .* Listening on port .*'
        - The expected error output has not been produced.
        - r'WARNING: .* Invalid value .* in '{option}' option. Default value will be used.'
    
    tags:
        - simulator
        - rids
    '''
    log_callback = callback_error_invalid_value_for('rids_closing_time', prefix=REMOTED_DETECTOR_PREFIX)
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")
