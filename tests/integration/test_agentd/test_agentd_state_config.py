'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-agentd' program is the client-side daemon that communicates with the server.
       These tests will check if the configuration options related to the statistics file of
       the 'fortishield-agentd' daemon are working properly. The statistics files are documents that
       show real-time information about the Fortishield environment.

components:
    - agentd

targets:
    - agent

daemons:
    - fortishield-agentd

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
    - https://fortishield.github.io/documentation/current/user-manual/reference/statistics-files/fortishield-agentd-state.html

tags:
    - stats_file
'''
import os
import sys
import time

import pytest
import yaml
from fortishield_testing import global_parameters
from fortishield_testing.agent import (set_state_interval,
                                 callback_state_interval_not_valid,
                                 callback_state_interval_not_found,
                                 callback_state_file_enabled,
                                 callback_state_file_not_enabled)
from fortishield_testing.fim import (change_internal_options)
from fortishield_testing.tools import LOG_FILE_PATH, FORTISHIELD_PATH
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.file import truncate_file
from fortishield_testing.tools.monitoring import FileMonitor
from fortishield_testing.tools.services import control_service, check_if_process_is_running

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.win32, pytest.mark.tier(level=0), pytest.mark.agent]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_data_file = os.path.join(test_data_path, 'fortishield_state_config_tests.yaml')
configurations_path = os.path.join(test_data_path, 'fortishield_conf.yaml')
configurations = load_fortishield_configurations(configurations_path, __name__)

# Open test cases description file
with open(test_data_file) as f:
    test_cases = yaml.safe_load(f)

# Variables
wait_daemon_control = 1

if sys.platform == 'win32':
    state_file_path = os.path.join(FORTISHIELD_PATH, 'fortishield-agent.state')
    internal_options = os.path.join(FORTISHIELD_PATH, 'internal_options.conf')
else:
    state_file_path = os.path.join(FORTISHIELD_PATH, 'var', 'run', 'fortishield-agentd.state')
    internal_options = os.path.join(FORTISHIELD_PATH, 'etc', 'internal_options.conf')

# ossec.log watch callbacks
callbacks = {
    'interval_not_valid': callback_state_interval_not_valid,
    'interval_not_found': callback_state_interval_not_found,
    'file_enabled': callback_state_file_enabled,
    'file_not_enabled': callback_state_file_not_enabled
}


# Fixture
@pytest.fixture(scope='module')
def set_local_internal_options():
    """Set local internal options"""
    if sys.platform == 'win32':
        change_internal_options('windows.debug', '2')
    else:
        change_internal_options('agent.debug', '2')
        
    yield
    
    if sys.platform == 'win32':
        change_internal_options('windows.debug', '0')
    else:
        change_internal_options('agent.debug', '0')
        
    set_state_interval(5, internal_options)


@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.parametrize('test_case',
                         [test_case['test_case'] for test_case in test_cases],
                         ids=[test_case['name'] for test_case in test_cases])
@pytest.mark.skipif(sys.platform == 'win32', reason="It will be blocked by #1593 and fortishield/fortishield#8746.")
def test_agentd_state_config(test_case, set_local_internal_options):
    '''
    description: Check that the 'fortishield-agentd.state' statistics file is created
                 automatically and verify that it is updated at the set intervals.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - test_case:
            type: list
            brief: List of tests to be performed.

    assertions:
        - Verify that the 'fortishield-agentd.state' statistics file has been created.
        - Verify that the 'fortishield-agentd.state' statistics file is updated at the specified intervals.

    input_description: An external YAML file (fortishield_conf.yaml) includes configuration settings for the agent.
                       Different test cases that are contained in an external YAML file (fortishield_state_config_tests.yaml)
                       that includes the parameters and their expected responses.

    expected_output:
        - r'interval_not_found'
        - r'interval_not_valid'
        - r'file_enabled'
        - r'file_not_enabled'
    '''
    control_service('stop', 'fortishield-agentd')

    # Truncate ossec.log in order to watch it correctly
    truncate_file(LOG_FILE_PATH)

    # Remove state file to check if agent behavior is as expected
    os.remove(state_file_path) if os.path.exists(state_file_path) else None

    # Set state interval value according to test case specs
    set_state_interval(test_case['interval'], internal_options)

    if sys.platform == 'win32':
        if test_case['agentd_ends']:
            with pytest.raises(ValueError):
                control_service('start')
            assert (test_case['agentd_ends']
                    is not check_if_process_is_running('fortishield-agentd'))
        else:
            control_service('start')
    else:
        control_service('start', 'fortishield-agentd')
        # Sleep enough time to Fortishield load agent.state_interval configuration and
        # boot fortishield-agentd
        time.sleep(wait_daemon_control) 
        assert (test_case['agentd_ends']
                    is not check_if_process_is_running('fortishield-agentd'))
    
    # Check if the test requires checking state file existence
    if 'state_file_exist' in test_case:
        if test_case['state_file_exist']:
            # Wait until state file was dumped
            time.sleep(test_case['interval'])
        assert test_case['state_file_exist'] == os.path.exists(state_file_path)

    # Follow ossec.log to find desired messages by a callback
    fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)
    fortishield_log_monitor.start(timeout=global_parameters.default_timeout,
                            callback=callbacks.get(test_case['log_expect']),
                            error_message='Event not found')
    assert fortishield_log_monitor.result()
