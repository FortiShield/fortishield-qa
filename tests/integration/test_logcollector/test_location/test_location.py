'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <info@fortishield.github.io>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector monitors the files that match
       the path set in the 'location' tag. The paths used will check several special situations
       that can occur when monitoring log files. Log data collection is the real-time process
       of making sense out of the records generated by servers or devices. This component can
       receive logs through text files or Windows event logs. It can also directly receive logs
       via remote syslog which is useful for firewalls and other such devices.

components:
    - logcollector

suite: location

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
    - Ubuntu Focal
    - Ubuntu Bionic
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://documentation.fortishield.github.io/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.fortishield.github.io/current/user-manual/reference/ossec-conf/localfile.html#location

tags:
    - logcollector_location
'''
import datetime
import os
import sys
import tempfile
import ast

import pytest
from fortishield_testing import logcollector
from fortishield_testing.tools import LOG_FILE_PATH
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.monitoring import FileMonitor

# Marks

pytestmark = pytest.mark.tier(level=0)

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'configuration_template')
configurations_path = os.path.join(test_data_path, 'configuration_location.yaml')
local_internal_options = {'logcollector.debug': '2'}

temp_dir = tempfile.gettempdir()

file_structure = [
    {
        'folder_path': os.path.join(temp_dir, 'fortishield-testing'),
        'filename': ['test.txt', 'foo.txt', 'bar.log', 'test.yaml', 'ñ.txt', 'Testing white spaces', 'test.log',
                     'c1test.txt', 'c2test.txt', 'c3test.txt', fr'file.log-%Y-%m-%d'],
        'content': f'Content of testing_file\n'
    },
    {
        'folder_path':  os.path.join(temp_dir, 'fortishield-testing', 'depth1'),
        'filename': ['depth_test.txt'],
        'content': f'Content of testing_file\n'
    },
    {
        'folder_path': os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'depth2'),
        'filename': ['depth_test.txt'],
        'content': f'Content of testing_file\n'
    },
    {
        'folder_path': os.path.join(temp_dir, 'fortishield-testing', 'duplicated'),
        'filename': ['duplicated.txt'],
        'content': f'Content of testing_file\n'
    },
    {
        'folder_path': os.path.join(temp_dir, 'fortishield-testing', 'multiple-logs'),
        'filename': [],
        'content': f'Content of testing_file\n'
    }
]

parameters = [
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'test.txt'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'depth1', ' depth_test.txt'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'depth2', 'depth_test.txt'),
     'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'non-existent.txt'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', '*'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'Testing white spaces'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'test.*'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'c*test.txt'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'duplicated', 'duplicated.txt'),
     'LOG_FORMAT': 'syslog', 'PATH_2': os.path.join(temp_dir, 'fortishield-testing', 'duplicated', 'duplicated.txt')},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', r'file.log-%Y-%m-%d'), 'LOG_FORMAT': 'syslog'},
    {'LOCATION': os.path.join(temp_dir, 'fortishield-testing', 'multiple-logs', '*'), 'LOG_FORMAT': 'syslog'}
]

metadata = [
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'test.txt'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'test.txt')],
     'log_format': 'syslog', 'file_type': 'single_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'depth1', ' depth_test.txt'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'depth1', ' depth_test.txt')],
     'log_format': 'syslog', 'file_type': 'single_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'depth2', 'depth_test.txt'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'depth1', 'depth2', 'depth_test.txt')],
     'log_format': 'syslog', 'file_type': 'single_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'non-existent.txt'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'non-existent.txt')],
     'log_format': 'syslog', 'file_type': 'non_existent_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', '*'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'foo.txt'),
               os.path.join(temp_dir, 'fortishield-testing', 'bar.log'),
               os.path.join(temp_dir, 'fortishield-testing', 'test.yaml'),
               os.path.join(temp_dir, 'fortishield-testing', 'ñ.txt')],
     'log_format': 'syslog', 'file_type': 'wildcard_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'Testing white spaces'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'Testing white spaces')], 'log_format': 'syslog',
     'file_type': 'single_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'test.*'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'test.txt'),
               os.path.join(temp_dir, 'fortishield-testing', 'test.log')],
     'log_format': 'syslog', 'file_type': 'wildcard_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'c*test.txt'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'c1test.txt'),
               os.path.join(temp_dir, 'fortishield-testing', 'c2test.txt'),
               os.path.join(temp_dir, 'fortishield-testing', 'c3test.txt')], 'log_format': 'syslog',
     'file_type': 'wildcard_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'duplicated', 'duplicated.txt'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'duplicated', 'duplicated.txt')],
     'log_format': 'syslog', 'path_2': os.path.join(temp_dir, 'fortishield-testing', 'duplicated', 'duplicated.txt'),
     'file_type': 'duplicated_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', r'file.log-%Y-%m-%d'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', r'file.log-%Y-%m-%d')], 'log_format': 'syslog',
     'file_type': 'single_file'},
    {'location': os.path.join(temp_dir, 'fortishield-testing', 'multiple-logs', '*'),
     'files': [os.path.join(temp_dir, 'fortishield-testing', 'multiple-logs', 'multiple')],
     'log_format': 'syslog', 'file_type': 'multiple_logs'}
]

if sys.platform != 'win32':
    for case in metadata:
        if case['location'] == os.path.join(temp_dir, 'fortishield-testing', '*'):
            for value in file_structure:
                if value['folder_path'] == os.path.join(temp_dir, 'fortishield-testing'):
                    value['filename'].append('テスト.txt')
                    value['filename'].append('ИСПЫТАНИЕ.txt')
                    value['filename'].append('测试.txt')
                    value['filename'].append('اختبار.txt')
            case['files'].append(os.path.join(temp_dir, 'fortishield-testing', 'テスト.txt'))
            case['files'].append(os.path.join(temp_dir, 'fortishield-testing', 'ИСПЫТАНИЕ.txt'))
            case['files'].append(os.path.join(temp_dir, 'fortishield-testing', '测试.txt'))
            case['files'].append(os.path.join(temp_dir, 'fortishield-testing', 'اختبار.txt'))

for value in file_structure:
    if value['folder_path'] == os.path.join(temp_dir, 'fortishield-testing', 'multiple-logs'):
        for i in range(2000):
            value['filename'].append(f'multiple{i}.txt')


# Configuration data
configurations = load_fortishield_configurations(configurations_path, __name__, params=parameters, metadata=metadata)
configuration_ids = [f"{x['LOCATION']}_{x['LOG_FORMAT']}" for x in parameters]
fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)


# Fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    date = datetime.date.today().strftime(r'%Y-%m-%d')
    test_case_real_paths_string = str(request.param).replace(r'file.log-%Y-%m-%d',  f"file.log-{date}")
    test_case_real_paths_dictionary = ast.literal_eval(test_case_real_paths_string)

    return test_case_real_paths_dictionary


@pytest.fixture(scope="module")
def get_files_list():
    """Get file list to create from the module."""
    return file_structure


@pytest.fixture(scope="module")
def location_file_date():
    """Get runtime test date."""
    global file_structure
    date = datetime.date.today().strftime(r'%Y-%m-%d')

    file_structure_string_real_paths = str(file_structure).replace(r'file.log-%Y-%m-%d',  f"file.log-{date}")
    file_structure = ast.literal_eval(file_structure_string_real_paths)


def test_location(location_file_date, get_files_list, create_file_structure_module, get_configuration,
                  configure_environment, configure_local_internal_options_module, file_monitoring,
                  restart_logcollector):
    '''
    description: Check if the 'fortishield-logcollector' monitors the log files specified in the 'location' tag.
                 For this purpose, the test will create a testing log file, configure a 'localfile' section
                 to monitor it, and set the 'location' tag with different values, including wildcards, inexistent
                 or duplicated files (depending on the test case). The test also will check if the file limit is
                 working by specifying a path that contains a log number that exceeds that limit. Finally, the test
                 will verify that the expected events are generated for those special situations.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_files_list:
            type: fixture
            brief: Get file list to create from the module.
        - create_file_structure_module:
            type: fixture
            brief: Create the specified file tree structure.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - configure_local_internal_options_module:
            type: fixture
            brief: Set internal configuration for testing.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
        - restart_logcollector:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.

    assertions:
        - Verify that the logcollector monitors a single log file specified in the 'location' tag.
        - Verify that the logcollector monitors a log file specified in the 'location' tag by a wildcard.
        - Verify that the logcollector detects an inexistent log file specified in the 'location' tag.
        - Verify that the logcollector detects a duplicated log file specified in the 'location' tag.
        - Verify that the logcollector detects when the number of monitored log files exceeds the limit.

    input_description: A configuration template (test_location) is contained in an external YAML file
                       (fortishield_location.yaml). That template is combined with different test cases defined
                       in the module. Those include configuration settings for the 'fortishield-logcollector' daemon.

    expected_output:
        - r'Analyzing file.*'
        - r'New file that matches the .* pattern.*'
        - r'Could not open file .*'
        - r'Log file .* is duplicated.'
        - r'File limit has been reached'

    tags:
        - logs
    '''
    file_type = get_configuration['metadata']['file_type']
    files = get_configuration['metadata']['files']

    for file_location in sorted(files):
        if file_type == 'single_file':
            log_callback = logcollector.callback_analyzing_file(file_location)
            log_monitor.start(timeout=logcollector.LOG_COLLECTOR_GLOBAL_TIMEOUT, callback=log_callback,
                              error_message=f"The expected 'Analyzing file {file_location}' message was not found")
        elif file_type == 'wildcard_file':
            pattern = get_configuration['metadata']['location']
            log_callback = logcollector.callback_match_pattern_file(pattern, file_location)
            log_monitor.start(timeout=logcollector.LOG_COLLECTOR_GLOBAL_TIMEOUT, callback=log_callback,
                              error_message=f"The expected 'New file that matches the '{pattern}' "
                              f"pattern: '{file_location}' message has not been produced")
        elif file_type == 'non_existent_file':
            log_callback = logcollector.callback_non_existent_file(file_location)
            log_monitor.start(timeout=logcollector.LOG_COLLECTOR_GLOBAL_TIMEOUT, callback=log_callback,
                              error_message="The expected 'Could not open file' message has not been produced")
        elif file_type == 'duplicated_file':
            log_callback = logcollector.callback_duplicated_file(file_location)
            log_monitor.start(timeout=logcollector.LOG_COLLECTOR_GLOBAL_TIMEOUT, callback=log_callback,
                              error_message=f"The expected 'Log file '{file_location}' is duplicated' "
                              f"message has not been produced")
        elif file_type == 'multiple_logs':
            log_callback = logcollector.callback_file_limit()

            try:
                fortishield_log_monitor.start(timeout=logcollector.LOG_COLLECTOR_GLOBAL_TIMEOUT, callback=log_callback,
                                        error_message=f"The expected 'File limit has been reached' "
                                                      f"message has not been produced")
            except Exception:
                if sys.platform == 'sunos5':
                    pytest.xfail(reason='Xfail due to issue: https://github.com/fortishield/fortishield/issues/10751')
