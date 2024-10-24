'''
copyright: Copyright (C) 2015-2023, Fortishield Inc.
           Created by Fortishield, Inc. <security@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: Integratord manages fortishield integrations with other applications such as Slack, Pagerduty, Shuffle, Yara or
       Virustotal by feeding the integrated aplications with the alerts located in alerts.json file. Custom values for
       fields can be configured to be sent using the 'options' tag. This test modules aim to test how the shuffle
       integration works with different configurations, when the options tag is not present or when custom values are
       passed into the tag for the shuffle integration

components:
    - integratord

suite: integration_options

targets:
    - manager

daemons:
    - fortishield-integratord

os_platform:
    - Linux

os_version:
    - Centos 8
    - Ubuntu Focal

references:
    - https://fortishield.github.io/documentation/current/user-manual/capabilities/virustotal-scan/integration.html
    - https://fortishield.github.io/documentation/current/user-manual/reference/daemons/fortishield-integratord.htm

pytest_args:
    - tier:
        0: Only level 0 tests are performed, they check basic functionalities and are quick to perform.
        1: Only level 1 tests are performed, they check functionalities of medium complexity.
        2: Only level 2 tests are performed, they check advanced functionalities and are slow to perform.

tags:
    - PagerDuty
'''
import os
import pytest

from fortishield_testing import global_parameters
from fortishield_testing.tools import LOG_FILE_PATH
from fortishield_testing.modules.integratord import event_monitor as evm
from fortishield_testing.tools.configuration import get_test_cases_data, load_configuration_template
from fortishield_testing.tools.monitoring import FileMonitor


# Marks
pytestmark = [pytest.mark.server]

# Reference paths
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIGURATIONS_PATH = os.path.join(TEST_DATA_PATH, 'configuration_template')
TEST_CASES_PATH = os.path.join(TEST_DATA_PATH, 'test_cases')

# Configuration and cases data
t1_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'config_pagerduty_no_option_tag.yaml')
t2_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'config_pagerduty_options.yaml')
t1_cases_path = os.path.join(TEST_CASES_PATH, 'cases_pagerduty_no_option_tag.yaml')
t2_cases_path = os.path.join(TEST_CASES_PATH, 'cases_pagerduty_options.yaml')

# Configurations
t1_configuration_parameters, t1_configuration_metadata, t1_case_ids = get_test_cases_data(t1_cases_path)
t1_configuration_parameters[0]['API_KEY'] = global_parameters.pagerduty_api_key
t1_configurations = load_configuration_template(t1_configurations_path, t1_configuration_parameters,
                                                t1_configuration_metadata)

t2_configuration_parameters, t2_configuration_metadata, t2_case_ids = get_test_cases_data(t2_cases_path)
for config_params in t2_configuration_parameters:
    config_params['API_KEY'] = global_parameters.pagerduty_api_key
t2_configurations = load_configuration_template(t2_configurations_path, t2_configuration_parameters,
                                                t2_configuration_metadata)

local_internal_options = {'integrator.debug': '2', 'analysisd.debug': '1', 'monitord.rotate_log': '0'}


# Tests
@pytest.mark.tier(level=1)
@pytest.mark.parametrize('configuration, metadata', zip(t1_configurations, t1_configuration_metadata), ids=t1_case_ids)
def test_pagerduty_no_option_tag(configuration, metadata, set_fortishield_configuration, truncate_monitored_files,
                                 configure_local_internal_options_module, restart_fortishield_daemon_function,
                                 wait_for_start_module):
    '''
    description: Check that when the options tag is not present for the PagerDuty integration, the integration works
                 properly.

    fortishield_min_version: 4.6.0

    test_phases:
        - setup:
            - Set fortishield configuration and local_internal_options.
            - Clean logs files and restart fortishield to apply the configuration.
        - test:
            - Check integration is enabled
            - Check no options JSON file is created
            - Check the message is sent to the PagerDuty server
            - Check the response code is 200
        - teardown:
            - Restore configuration
            - Stop fortishield

    tier: 1

    parameters:
        - configuration:
            type: dict
            brief: Configuration loaded from `configuration_template`.
        - metadata:
            type: dict
            brief: Test case metadata.
        - set_fortishield_configuration:
            type: fixture
            brief: Set fortishield configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate all the log files and json alerts files before and after the test execution.
        - configure_local_internal_options_module:
            type: fixture
            brief: Configure the local internal options file.
        - restart_fortishield_daemon_function:
            type: fixture
            brief: Restart fortishield daemon before starting a test.
        - wait_for_start_module:
            type: fixture
            brief: Detect the start of the Integratord module

    assertions:
        - Verify the integration is enabled
        - Verify no options JSON file is detected
        - Verify the integration sends message to the integrated app's server
        - Verify the response code from the integrated app

    input_description:
        - The `config_integration_no_option_tag.yaml` file provides the module configuration for this test.
        - The `cases_integration_no_option_tag_alerts` file provides the test cases.

    expected_output:
        - ".*(Enabling integration for: '{integration}')."
        - ".*ERROR: Unable to run integration for ({integration}) -> integrations"
        - '.*OS_IntegratorD.*(JSON file for options  doesn't exist)'
        - '.*Response received.* [200].*'
    '''
    fortishield_monitor = FileMonitor(LOG_FILE_PATH)

    # Check integration is enabled
    evm.detect_integration_enabled(integration=metadata['integration'], file_monitor=fortishield_monitor)

    # Check no options JSON file is detected
    evm.detect_options_json_file_does_not_exist(file_monitor=fortishield_monitor)

    # Check the message is sent to the integration's server
    evm.get_message_sent(integration='PagerDuty', file_monitor=fortishield_monitor)

    # Check the response code from the integration's server
    evm.check_third_party_response(file_monitor=fortishield_monitor, timeout=global_parameters.default_timeout)


@pytest.mark.tier(level=1)
@pytest.mark.parametrize('configuration, metadata', zip(t2_configurations, t2_configuration_metadata), ids=t2_case_ids)
def test_pagerduty_options(configuration, metadata, set_fortishield_configuration, truncate_monitored_files,
                           configure_local_internal_options_module, restart_fortishield_daemon_function,
                           wait_for_start_module):
    '''
    description: Check that when configuring the options tag with differents values, the integration works as expected.
                 The test also checks that when it is supposed to fail, it fails.

    fortishield_min_version: 4.6.0

    test_phases:
        - setup:
            - Set fortishield configuration and local_internal_options.
            - Clean logs files and restart fortishield to apply the configuration.
        - test:
            - Check integration is enabled
            - Check the integration is unable to run when expected
            - Check the integration sends the message and gets a response when expected
        - teardown:
            - Restore configuration
            - Stop fortishield

    tier: 1

    parameters:
        - configuration:
            type: dict
            brief: Configuration loaded from `configuration_template`.
        - metadata:
            type: dict
            brief: Test case metadata.
        - set_fortishield_configuration:
            type: fixture
            brief: Set fortishield configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate all the log files and json alerts files before and after the test execution.
        - configure_local_internal_options_module:
            type: fixture
            brief: Configure the local internal options file.
        - restart_fortishield_daemon_function:
            type: fixture
            brief: Restart fortishield daemon before starting a test.
        - wait_for_start_module:
            type: fixture
            brief: Detect the start of the Integratord module

    assertions:
        - Verify the integration is enabled
        - Verify no options JSON file is detected
        - Verify the integration sends message to the integrated app's server
        - Verify the response code from the integrated app


    input_description:
        - The `config_PagerDuty_options.yaml` file provides the module configuration for this test.
        - The `cases_PagerDuty_options.yaml` file provides the test cases.

    expected_output:
        - ".*(Enabling integration for: '{integration}')."
        - ".*ERROR: Unable to run integration for ({integration}) -> integrations"
        - '.*OS_IntegratorD.*(JSON file for options  doesn't exist)'
        - '.*Response received.* [200].*'

    '''
    fortishield_monitor = FileMonitor(LOG_FILE_PATH)

    # Check if the integration is enabled
    evm.detect_integration_enabled(integration=metadata['integration'], file_monitor=fortishield_monitor)

    if not metadata['sends_message']:
        # Check the integration is unable to run when it should.
        evm.detect_unable_to_run_integration(integration=metadata['integration'], file_monitor=fortishield_monitor)
    else:
        # Verify that the message is sent
        message = evm.get_message_sent(integration='PagerDuty', file_monitor=fortishield_monitor)

        # Verify that when the options JSON was not empty the sent information is in the response message.
        if metadata['added_option'] is not None:
            assert metadata['added_option'] in message, "The configured option is not present in the message sent"

        # Check the response code from the integration's server
        evm.check_third_party_response(file_monitor=fortishield_monitor, timeout=global_parameters.default_timeout)
