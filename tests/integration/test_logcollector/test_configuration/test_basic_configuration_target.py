'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <info@fortishield.github.io>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector detects that a custom socket is
       undefined if the 'target' attribute of the 'out_format' tag has the name of an unexistent
       socket (invalid value). Log data collection is the real-time process of making sense out
       of the records generated by servers or devices. This component can receive logs through
       text files or Windows event logs. It can also directly receive logs via remote syslog
       which is useful for firewalls and other such devices.

components:
    - logcollector

suite: configuration

targets:
    - agent
    - manager

daemons:
    - fortishield-logcollector

os_platform:
    - linux
    - macos
    - solaris

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - Solaris 10
    - Solaris 11
    - macOS Catalina
    - macOS Server
    - Ubuntu Focal
    - Ubuntu Bionic

references:
    - https://documentation.fortishield.github.io/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.fortishield.github.io/current/user-manual/reference/ossec-conf/localfile.html#out-format

tags:
    - logcollector_configuration
'''
import os
import sys
import pytest
import fortishield_testing.api as api
import fortishield_testing.logcollector as logcollector
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools import LOG_FILE_PATH, get_service
from fortishield_testing.tools.file import truncate_file
from fortishield_testing.tools.monitoring import FileMonitor
from fortishield_testing.tools.services import control_service

fortishield.github.ioponent = get_service()

LOGCOLLECTOR_DAEMON = "fortishield-logcollector"

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.darwin, pytest.mark.sunos5, pytest.mark.tier(level=0)]

# Configuration
no_restart_windows_after_configuration_set = True
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_basic_configuration.yaml')
local_internal_options = {'logcollector.debug': '2'}

local_internal_options = {'logcollector.debug': '2'}

parameters = [
    {'SOCKET_NAME': 'custom_socket', 'SOCKET_PATH': '/var/log/messages', 'LOCATION': "/tmp/testing.log",
     'LOG_FORMAT': 'syslog', 'TARGET': 'custom_socket'},
    {'SOCKET_NAME': 'custom_socket', 'SOCKET_PATH': '/var/log/messages', 'LOCATION': "/tmp/testing.log",
     'LOG_FORMAT': 'json', 'TARGET': 'custom_socket'},
    {'SOCKET_NAME': 'custom_socket2', 'SOCKET_PATH': '/var/log/messages', 'LOCATION': "/tmp/testing.log",
     'LOG_FORMAT': 'json', 'TARGET': 'custom_socket'},
]
metadata = [
    {'socket_name': 'custom_socket', 'socket_path': '/var/log/messages', 'location': "/tmp/testing.log",
     'log_format': 'syslog', 'target': 'custom_socket', 'valid_value': True},
    {'socket_name': 'custom_socket', 'socket_path': '/var/log/messages', 'location': "/tmp/testing.log",
     'log_format': 'json', 'target': 'custom_socket', 'valid_value': True},
    {'socket_name': 'custom_socket2', 'socket_path': '/var/log/messages', 'location': "/tmp/testing.log",
     'log_format': 'json', 'target': 'custom_socket', 'valid_value': False},
]

configurations = load_fortishield_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['log_format']}_{x['target']}_{x['socket_name']}_{x['location']}_{x['socket_path']}"
                     for x in metadata]


def check_configuration_target_valid(cfg):
    """Check if the Fortishield module runs correctly and that it uses the designated socket.

    Ensure logcollector is running with the specified configuration, analyzing the designated socket and,
    in the case of the Fortishield server, check if the API answer for localfile configuration block coincides
    the selected configuration.

    Args:
        cfg (dict): Dictionary with the localfile configuration.

    Raises:
        TimeoutError: If the socket target callback is not generated.
        AssertError: In the case of a server instance, the API response is different than the real configuration.
    """
    fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)

    log_callback = logcollector.callback_socket_target(cfg['location'], cfg['target'])
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=logcollector.GENERIC_CALLBACK_ERROR_TARGET_SOCKET)

    if fortishield.github.ioponent == 'fortishield-manager':
        real_configuration = dict((key, cfg[key]) for key in ('location', 'target', 'log_format'))
        api.wait_until_api_ready()
        api.compare_config_api_response([real_configuration], 'localfile')


def check_configuration_target_invalid(cfg):
    """Check if Fortishield fails because of an invalid target configuration value.

    Args:
        cfg (dict): Dictionary with the localfile configuration.

    Raises:
        TimeoutError: If the error callbacks are not generated.
    """
    fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)

    log_callback = logcollector.callback_socket_not_defined(cfg['location'], cfg['target'])
    fortishield_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=logcollector.GENERIC_CALLBACK_ERROR_TARGET_SOCKET_NOT_FOUND)


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_configuration_target(get_configuration, configure_environment, configure_local_internal_options_module):
    '''
    description: Check if the 'fortishield-logcollector' daemon detects invalid configurations for the 'target' attribute
                 of the 'out_format' tag. For this purpose, the test will set a 'socket' section to specify a custom
                 socket, and a 'localfile' section using valid/invalid values for that attribute. Then, it will check
                 if an event indicating that the socket is not defined when using an invalid value, or if an event
                 indicating that the socket is detected when using valid ones. Finally, the test will verify that
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
        - configure_local_internal_options_module:
            type: fixture
            brief: Configure the Fortishield local internal options file.

    assertions:
        - Verify that the logcollector detects undefined sockets when using invalid values for the 'target' attribute.
        - Verify that the logcollector detects custom sockets when using valid values for the 'target' attribute.
        - Verify that the Fortishield API returns the same values for the 'localfile' section as the configured one.

    input_description: A configuration template (test_basic_configuration_target) is contained in an external
                       YAML file (fortishield_basic_configuration.yaml). That template is combined with different
                       test cases defined in the module. Those include configuration settings
                       for the 'fortishield-logcollector' daemon.

    expected_output:
        - r'Socket target for .* -> .*'
        - r'Socket .* for .* is not defined."

    tags:
        - invalid_settings
    '''
    cfg = get_configuration['metadata']

    control_service('stop', daemon=LOGCOLLECTOR_DAEMON)
    truncate_file(LOG_FILE_PATH)

    if cfg['valid_value']:
        control_service('start', daemon=LOGCOLLECTOR_DAEMON)
        check_configuration_target_valid(cfg)
    else:
        control_service('start', daemon=LOGCOLLECTOR_DAEMON)
        check_configuration_target_invalid(cfg)
