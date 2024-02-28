'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the 'age' option work as expected, ignoring files
       that have not been modified for a time greater than the 'age' value when the system datetime
       is changed while the logcollector process is running.
       Log data collection is the real-time process of making sense out of the records generated by
       servers or devices. This component can receive logs through text files or Windows event logs.
       It can also directly receive logs via remote syslog which is useful for firewalls and
       other such devices.

components:
    - logcollector

suite: age

targets:
    - agent
    - manager

daemons:
    - fortishield-logcollector

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
    - Solaris 10
    - Solaris 11
    - macOS Catalina
    - macOS Server
    - Ubuntu Focal
    - Ubuntu Bionic
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://fortishield.github.io/documentation/current/user-manual/capabilities/log-data-collection/index.html
    - https://fortishield.github.io/documentation/current/user-manual/reference/ossec-conf/localfile.html#age

tags:
    - logcollector_age
'''
import os
import sys
import time
import tempfile
from datetime import datetime

import pytest

import fortishield_testing.logcollector as logcollector
from fortishield_testing.tools import get_service
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.services import control_service
from fortishield_testing.tools.time import TimeMachine, time_to_timedelta, time_to_seconds
from fortishield_testing.tools.utils import lower_case_key_dictionary_array


# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_age.yaml')

DAEMON_NAME = "fortishield-logcollector"

local_internal_options = {'logcollector.vcheck_files': '0', 'logcollector.debug': '2', 'monitord.rotate_log': '0',
                          'windows.debug': '2'}

timeout_logcollector_read = 10
now_date = datetime.now()
folder_path = os.path.join(tempfile.gettempdir(), 'fortishield_testing_age')
folder_path_regex = os.path.join(folder_path, '*')
timeout_file_read = 4

file_structure = [
    {
        'folder_path': folder_path,
        'filename': ['testing_age_dating.log'],
    }
]

parameters = [
    {'LOCATION': folder_path_regex, 'LOG_FORMAT': 'syslog', 'AGE': '4000s'},
    {'LOCATION': folder_path_regex, 'LOG_FORMAT': 'syslog', 'AGE': '5m'},
    {'LOCATION': folder_path_regex, 'LOG_FORMAT': 'syslog', 'AGE': '500m'},
    {'LOCATION': folder_path_regex, 'LOG_FORMAT': 'syslog', 'AGE': '9h'},
    {'LOCATION': folder_path_regex, 'LOG_FORMAT': 'syslog', 'AGE': '200d'},
]

metadata = lower_case_key_dictionary_array(parameters)

new_host_datetime = ['60s', '-60s', '30m', '-30m', '2h', '-2h', '43d', '-43d']

configurations = load_fortishield_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)

configuration_ids = [f"{x['location']}_{x['log_format']}_{x['age']}" for x in metadata]


@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.fixture(scope="function")
def get_files_list():
    """Get file list to create from the module."""
    return file_structure


@pytest.fixture(scope='function')
def restart_logcollector_function():
    """Reset log file and start a new monitor."""
    control_service('restart', daemon=DAEMON_NAME)


@pytest.mark.parametrize('new_datetime', new_host_datetime)
@pytest.mark.skip("Skipped by Issue #3218")
def test_configuration_age_datetime(get_configuration, configure_environment, configure_local_internal_options_module,
                                    restart_monitord, restart_logcollector_function, file_monitoring,
                                    new_datetime, get_files_list, create_file_structure_function):
    '''
    description: Check if the 'fortishield-logcollector' daemon ignores the monitored files that have not been modified
                 for a time greater than the value set in the 'age' tag, and the system datetime is changed. For
                 this purpose, the test will create a folder with a testing log file to be monitored and configure
                 different values for the 'age' option. Once the logcollector has started, it will change the system
                 datetime and wait for the event that indicates that the log file is being monitored. Finally,
                 depending on the 'age' value, the test will verify that the 'ignore' event is triggered or not
                 and restore the system datetime to its initial value.

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
            brief: Configure the Fortishield local internal options.
        - restart_monitord:
            type: fixture
            brief: Reset the log file and start a new monitor.
        - restart_logcollector_function:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
        - new_datetime:
            type: str
            brief: Time to forward/backward the current datetime.
        - get_files_list:
            type: fixture
            brief: Get file list to create from the module.
        - create_file_structure_function:
            type: fixture
            brief: Create the specified file tree structure.

    assertions:
        - Verify that the logcollector detects the testing log file to monitor.
        - Verify that the logcollector ignores the monitored files that have not been modified
          for a time greater than the 'age' value.
        - Verify that the logcollector does not ignore the monitored files that have been modified
          for a time greater than the 'age' value.

    input_description: A configuration template (test_age) is contained in an external YAML file (fortishield_age.yaml),
                       which includes configuration settings for the 'fortishield-logcollector' daemon and, it is combined
                       with the test cases (settings, time offset, and files to monitor) defined in the module.

    expected_output:
        - r'New file that matches the .* pattern.*'
        - r'DEBUG: Ignoring file .* due to modification time''

    tags:
        - logs
        - time_travel
    '''
    cfg = get_configuration['metadata']
    age_seconds = time_to_seconds(cfg['age'])

    control_service('restart')

    time.sleep(timeout_logcollector_read)

    TimeMachine.travel_to_future(time_to_timedelta(new_datetime))

    for file in file_structure:
        for name in file['filename']:
            absolute_file_path = os.path.join(file['folder_path'], name)

            log_callback = logcollector.callback_match_pattern_file(cfg['location'], absolute_file_path)
            log_monitor.start(timeout=10, callback=log_callback,
                              error_message=f"{name} was not detected")

            fileinfo = os.stat(absolute_file_path)
            current_time = time.time()
            mfile_time = current_time - fileinfo.st_mtime

            if age_seconds <= int(mfile_time):
                log_callback = logcollector.callback_ignoring_file(absolute_file_path)
                log_monitor.start(timeout=30, callback=log_callback,
                                  error_message=f"{name} was not ignored")
            else:
                with pytest.raises(TimeoutError):
                    log_callback = logcollector.callback_ignoring_file(absolute_file_path)
                    log_monitor.start(timeout=5, callback=log_callback,
                                      error_message=f"{name} was not ignored")

        TimeMachine.time_rollback()
