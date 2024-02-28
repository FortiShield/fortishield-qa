'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.
           Created by Fortishield, Inc. <security@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-remoted' program is the server side daemon that communicates with the agents.
       Specifically, this test will check that 'fortishield-remoted' doesn't start and produces an error
       message when 'allowed-ips' values are invalid.

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
    - https://fortishield.github.io/documentation/current/user-manual/reference/daemons/fortishield-remoted.html
    - https://fortishield.github.io/documentation/current/user-manual/reference/ossec-conf/remote.html
    - https://fortishield.github.io/documentation/current/user-manual/agents/agent-life-cycle.html
    - https://fortishield.github.io/documentation/current/user-manual/capabilities/agent-key-polling.html

tags:
    - remoted
'''
import os
import pytest

import fortishield_testing.remote as remote
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.monitoring import REMOTED_DETECTOR_PREFIX
import fortishield_testing.generic_callbacks as gc
from fortishield_testing.tools import FORTISHIELD_CONF_RELATIVE

# Marks
pytestmark = [pytest.mark.server, pytest.mark.tier(level=0)]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_basic_configuration.yaml')

parameters = [
    {'ALLOWED': '127.0.0.0.0'},
    {'ALLOWED': 'Testing'},
    {'ALLOWED': '127.0.0.0/7890'},
    {'ALLOWED': '127.0.0.0/7890'},
    {'ALLOWED': '::1::1'},
    {'ALLOWED': 'Testing'},
    {'ALLOWED': '::1/512'},
    {'ALLOWED': '::1/512'}
]

metadata = [
    {'allowed-ips': '127.0.0.0.0'},
    {'allowed-ips': 'Testing'},
    {'allowed-ips': '127.0.0.0/7890'},
    {'allowed-ips': '127.0.0.0/7890'},
    {'allowed-ips': '::1::1'},
    {'allowed-ips': 'Testing'},
    {'allowed-ips': '::1/512'},
    {'allowed-ips': '::1/512'}
]

configurations = load_fortishield_configurations(configurations_path, "test_allowed_ips_invalid",
                                           params=parameters, metadata=metadata)
configuration_ids = [f"{x['ALLOWED']}" for x in parameters]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_allowed_ips_invalid(get_configuration, configure_environment, restart_remoted):
    '''
    description: Check that 'fortishield-remoted' fails when 'allowed-ips' has invalid values.
                 For this purpose, it uses the configuration from test cases and check if the different errors are
                 logged correctly.
    
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
        - Verify that the errors is logged correctly in ossec.log whent they should be.
    
    input_description: A configuration template (test_basic_configuration_allowed_denied_ips) is contained in an
                       external YAML file, (fortishield_basic_configuration.yaml). That template is combined with different
                       test cases defined in the module. Those include configuration settings for the 'fortishield-remoted'
                       daemon and agents info.
    
    expected_output:
        - r'Started <pid>: .* Listening on port .*'
        - The expected error output has not been produced.
        - r'ERROR: .* Invalid ip address:.*'
        - r'(ERROR|CRITICAL): .* Configuration error at '.*'
    
    tags:
        - remoted
    '''
    cfg = get_configuration['metadata']

    log_callback = remote.callback_error_invalid_ip(cfg['allowed-ips'])
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")

    log_callback = gc.callback_error_in_configuration('ERROR', prefix=REMOTED_DETECTOR_PREFIX,
                                                      conf_path=FORTISHIELD_CONF_RELATIVE)
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")

    log_callback = gc.callback_error_in_configuration('CRITICAL', prefix=REMOTED_DETECTOR_PREFIX,
                                                      conf_path=FORTISHIELD_CONF_RELATIVE)
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")
