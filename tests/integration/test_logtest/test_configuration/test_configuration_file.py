'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <info@fortishield.github.io>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logtest' tool allows the testing and verification of rules and decoders against provided log examples
       remotely inside a sandbox in 'fortishield-analysisd'. This functionality is provided by the manager, whose work
       parameters are configured in the ossec.conf file in the XML rule_test section. Test logs can be evaluated through
       the 'fortishield-logtest' tool or by making requests via RESTful API. These tests will check if the logtest
       configuration is valid. Also checks rules, decoders, decoders, alerts matching logs correctly.

components:
    - logtest

suite: configuration

targets:
    - manager

daemons:
    - fortishield-analysisd

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
    - https://documentation.fortishield.github.io/current/user-manual/reference/tools/fortishield-logtest.html
    - https://documentation.fortishield.github.io/current/user-manual/capabilities/fortishield-logtest/index.html
    - https://documentation.fortishield.github.io/current/user-manual/reference/daemons/fortishield-analysisd.html

tags:
    - logtest_configuration
'''
import os
import pytest

from fortishield_testing import global_parameters
from fortishield_testing.logtest import (callback_logtest_started, callback_logtest_disabled, callback_configuration_error)
from fortishield_testing.tools import LOG_FILE_PATH
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.monitoring import FileMonitor

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_conf.yaml')
configurations = load_fortishield_configurations(configurations_path, __name__)

# Variables
fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)


# Fixture
@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# Test
def test_configuration_file(get_configuration, configure_environment, restart_fortishield):
    '''
    description: Checks if `fortishield-logtest` works as expected under different predefined configurations that cause
                 `fortishield-logtest` to start correctly, to be disabled, or to register an error. To do this, it checks
                 some values in these configurations from 'fortishield_conf.yaml' file.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configuration from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing
        - restart_fortishield:
            type: fixture
            brief: Restart fortishield, ossec.log and start a new monitor.

    assertions:
        - Verify that a valid configuration is loaded.
        - Verify that wrong loaded configurations lead to an error.

    input_description: Five test cases are defined in the module. These include some configurations stored in
                       the 'fortishield_conf.yaml'.

    expected_output:
        - r'.* Logtest started'
        - r'.* Logtest disabled'
        - r'.* Invalid value for element'
        - 'Event not found'

    tags:
        - settings
        - analysisd
    '''
    callback = None
    if 'valid_conf' in get_configuration['tags']:
        callback = callback_logtest_started
    elif 'disabled_conf' in get_configuration['tags']:
        callback = callback_logtest_disabled
    else:
        callback = callback_configuration_error

    fortishield_log_monitor.start(timeout=global_parameters.default_timeout, callback=callback,
                            error_message='Event not found')
