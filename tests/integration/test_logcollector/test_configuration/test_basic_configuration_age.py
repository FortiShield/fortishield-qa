'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector detects invalid values for the 'age'
       tag and the Fortishield API returns the same values for the configured 'localfile' section.
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
    - https://fortishield.github.io/documentation/current/user-manual/capabilities/log-data-collection/index.html
    - https://fortishield.github.io/documentation/current/user-manual/reference/ossec-conf/localfile.html#age

tags:
    - logcollector_configuration
'''
import os
import pytest
import sys
import fortishield_testing.api as api
from fortishield_testing.tools import get_service
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.monitoring import LOG_COLLECTOR_DETECTOR_PREFIX, WINDOWS_AGENT_DETECTOR_PREFIX
import fortishield_testing.generic_callbacks as gc
import fortishield_testing.logcollector as logcollector
from fortishield_testing.tools.monitoring import FileMonitor
from fortishield_testing.tools import LOG_FILE_PATH
from fortishield_testing.tools.file import truncate_file
from fortishield_testing.tools.services import control_service
import subprocess as sb

LOGCOLLECTOR_DAEMON = "fortishield-logcollector"

# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_basic_configuration.yaml')
fortishield.github.ioponent = get_service()


if sys.platform == 'win32':
    location = r'C:\testing\file.txt'
    fortishield_configuration = 'ossec.conf'
    prefix = WINDOWS_AGENT_DETECTOR_PREFIX
    no_restart_windows_after_configuration_set = True
    force_restart_after_restoring = True

else:
    location = '/tmp/testing.txt'
    fortishield_configuration = 'etc/ossec.conf'
    prefix = LOG_COLLECTOR_DETECTOR_PREFIX

parameters = [
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '3s'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '4000s'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '5m'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '99h'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '94201d'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '44sTesting'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': 'Testing44s'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '9hTesting'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '400mTesting'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': '3992'},
    {'LOCATION': f'{location}', 'LOG_FORMAT': 'syslog', 'AGE': 'Testing'},
]
metadata = [
    {'location': f'{location}', 'log_format': 'syslog', 'age': '3s', 'valid_value': True},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '4000s', 'valid_value': True},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '5m', 'valid_value': True},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '99h', 'valid_value': True},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '94201d', 'valid_value': True},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '44sTesting', 'valid_value': False},
    {'location': f'{location}', 'log_format': 'syslog', 'age': 'Testing44s', 'valid_value': False},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '9hTesting', 'valid_value': False},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '400mTesting', 'valid_value': False},
    {'location': f'{location}', 'log_format': 'syslog', 'age': '3992', 'valid_value': False},
    {'location': f'{location}', 'log_format': 'syslog', 'age': 'Testing', 'valid_value': False},
]

problematic_values = ['44sTesting', '9hTesting', '400mTesting', '3992']
configurations = load_fortishield_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['location']}_{x['log_format']}_{x['age']}" for x in metadata]


def check_configuration_age_valid(cfg):
    """Check if the Fortishield module runs correctly and analyze the desired file.

    Ensure logcollector is running with the specified configuration, analyzing the designated file and,
    in the case of the Fortishield server, check if the API answer for localfile configuration block coincides
    the selected configuration.

    Args:
        cfg (dict): Dictionary with the localfile configuration.

    Raises:
        TimeoutError: If the "Analyzing file" callback is not generated.
        AssertError: In the case of a server instance, the API response is different from real configuration.
    """
    fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)

    log_callback = logcollector.callback_analyzing_file(cfg['location'])
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_FILE)
    if fortishield.github.ioponent == 'fortishield-manager':
        real_configuration = cfg.copy()
        real_configuration.pop('valid_value')
        api.wait_until_api_ready()
        api.compare_config_api_response([real_configuration], 'localfile')


def check_configuration_age_invalid(cfg):
    """Check if the Fortishield fails because the invalid age configuration value.

    Args:
        cfg (dict): Dictionary with the localfile configuration.

    Raises:
        TimeoutError: If error callback are not generated.
    """
    fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)

    log_callback = gc.callback_invalid_conf_for_localfile('age', prefix, severity='ERROR')
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=gc.GENERIC_CALLBACK_ERROR_MESSAGE)
    log_callback = gc.callback_error_in_configuration('ERROR', prefix,
                                                      conf_path=f'{fortishield_configuration}')
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=gc.GENERIC_CALLBACK_ERROR_MESSAGE)

    if sys.platform != 'win32':
        log_callback = gc.callback_error_in_configuration('CRITICAL', prefix,
                                                          conf_path=f'{fortishield_configuration}')
        fortishield_log_monitor.start(timeout=5, callback=log_callback,
                                error_message=gc.GENERIC_CALLBACK_ERROR_MESSAGE)


@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.skip("This test needs refactor/fixes. Has flaky behaviour. Skipped by Issue #3218")
@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_configuration_age(get_configuration, configure_environment):
    '''
    description: Check if the 'fortishield-logcollector' daemon detects invalid configurations for the 'age' tag.
                 For this purpose, the test will set a 'localfile' section using valid/invalid values for that
                 tag. Then, it will check if the 'analyzing' event is triggered when using a valid value, or
                 if an error event is generated when using an invalid one. Finally, the test will verify that
                 the Fortishield API returns the same values for the 'localfile' section that the configured one.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.

    assertions:
        - Verify that the logcollector generates error events when using invalid values for the 'age' tag.
        - Verify that the logcollector generates 'analyzing' events when using valid values for the 'age' tag.
        - Verify that the Fortishield API returns the same values for the 'localfile' section as the configured one.

    input_description: A configuration template (test_basic_configuration_age) is contained in an external YAML file
                       (fortishield_basic_configuration.yaml). That template is combined with different test cases defined
                       in the module. Those include configuration settings for the 'fortishield-logcollector' daemon.

    expected_output:
        - r'Analyzing file.*'
        - r'Invalid .* for localfile'
        - r'Configuration error at .*'

    tags:
        - invalid_settings
    '''
    cfg = get_configuration['metadata']

    control_service('stop', daemon=LOGCOLLECTOR_DAEMON)
    truncate_file(LOG_FILE_PATH)

    if cfg['valid_value']:
        control_service('start', daemon=LOGCOLLECTOR_DAEMON)
        check_configuration_age_valid(cfg)
    else:
        if cfg['age'] in problematic_values:
            pytest.xfail("Logcollector accepts invalid values: https://github.com/fortishield/fortishield/issues/8158")
        else:
            if sys.platform == 'win32':
                pytest.xfail("Windows agent allows invalid localfile configuration:\
                              https://github.com/fortishield/fortishield/issues/10890")
                expected_exception = ValueError
            else:
                expected_exception = sb.CalledProcessError

            with pytest.raises(expected_exception):
                control_service('start', daemon=LOGCOLLECTOR_DAEMON)
                check_configuration_age_invalid(cfg)
