'''
copyright: Copyright (C) 2015-2021, Wazuh Inc.
           Created by Wazuh, Inc. <info@wazuh.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
type: integration
brief: There is an API configuration option, called logs, which allows to log in 4 different ways ("json", "plain",
       "json,plain", and "plain,json") through the format field. When the API is configured with one of those values the
       logs are stored in the api.log and api.json files.
tier: 2
modules:
    - api
components:
    - manager
daemons:
    - wazuh-apid
os_platform:
    - linux
os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - CentOS 6
    - Ubuntu Focal
    - Ubuntu Bionic
    - Ubuntu Xenial
    - Ubuntu Trusty
    - Debian Buster
    - Debian Stretch
    - Debian Jessie
    - Debian Wheezy
    - Red Hat 8
    - Red Hat 7
    - Red Hat 6
references:
    - https://documentation.wazuh.com/current/user-manual/api/configuration.html#logs
tags:
    - api
    - logs
    - logging
'''
import os
import re

import requests
import pytest

from wazuh_testing.tools import PREFIX, API_LOG_FILE_PATH, API_JSON_LOG_FILE_PATH
from wazuh_testing.tools.configuration import get_api_conf
from wazuh_testing.tools.monitoring import FileMonitor
from wazuh_testing.api import API_PROTOCOL, API_HOST, API_PORT, API_USER, API_PASS, API_LOGIN_ENDPOINT, \
    API_GLOBAL_TIMEOUT, get_login_headers

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=2)]

# Variables
daemons_handler_configuration = {'all_daemons': True}
test_directories = [os.path.join(PREFIX, 'test_logs')]
error_log_payload = 'Timeout executing API request'

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'configuration_api_logs_format.yaml')
configurations = get_api_conf(configurations_path)
tcase_ids = [f"level_{configuration['configuration']['logs']['level']}" +  \
             f"_format_{configuration['configuration']['logs']['format']}" for  configuration in configurations]

# Fixtures
@pytest.fixture(scope='module', params=configurations, ids=tcase_ids)
def get_configuration(request):
    """Get configurations from the module."""

    return request.param


def send_request(login_attempts=5):
    """Send a login request to the API."""

    login_url = f"{API_PROTOCOL}://{API_HOST}:{API_PORT}{API_LOGIN_ENDPOINT}"

    for _ in range(login_attempts):
        response = requests.get(login_url, headers=get_login_headers(API_USER, API_PASS), verify=False,
                                timeout=API_GLOBAL_TIMEOUT)
        if response.status_code == 200: return True


def callback_json_log_login_info(line):
    """Match a given line with a regular expression."""

    payload = r'"user": "wazuh", "ip": "127.0.0.1", "http_method": "GET", "uri": "GET ' + f'{API_LOGIN_ENDPOINT}"' + \
              r', "parameters": {}' + r', "body": {}' + \
              r', "time": "(\d*\.*\d+)s", "status_code": (\d+)'
    msg = r'{"timestamp": "(\d+\/\d+\/\d+ \d+:\d+:\d+)", "levelname": "INFO", "data": {"type": "request", ' \
          r'"payload": {' + f'{payload}' + r'}}}'
    match = re.match(msg, line)
    return match


def callback_plain_log_login_info(line):
    """Match a given line with a regular expression."""

    msg = fr'(\d+/\d+/\d+ \d+:\d+:\d+) INFO: wazuh 127.0.0.1 "GET {API_LOGIN_ENDPOINT}" with parameters' \
          r' {} and body {} done in (\d*\.*\d+)s: (\d+)'
    match = re.match(msg, line)
    return match


def callback_json_log_error(line):
    """Match a given line with a regular expression."""

    msg = r'{"timestamp": "(\d+/\d+/\d+ \d+:\d+:\d+)", "levelname": "ERROR", "data": {"type": "informative", ' \
          fr'"payload": "{error_log_payload}"}}'
    match = re.match(msg, line)
    return match


def callback_plain_error(line):
    """Match a given line with a regular expression."""

    msg = fr"(\d+/\d+/\d+ \d+:\d+:\d+) ERROR: {error_log_payload}"
    match = re.match(msg, line)
    return match


# Tests
@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_api_logs_formats(get_configuration, configure_api_environment, clean_log_files, daemons_handler,
                          wait_for_start):
    '''
    description: The test checks if the logs of the API are stored in the specified formats and the content of the log
                 files are the expected.
    wazuh_min_version: 4.4.0
    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_api_environment:
            type: fixture
            brief: Configure a custom environment for API testing.
        - clean_log_files:
            type: fixture
            brief: Reset the log files of the API and delete the rotated log files.
        - daemons_handler:
            type: fixture
            brief: Handle the Wazuh daemons.
        - wait_for_start:
            type: fixture
            brief: Wait until the API starts.
    assertions:
        - Verify that the expected log exists in the log file.
        - Verify that the logs values are the same in both log formats.
    input_description: The test gets the configuration from the YAML file, which contains the API configuration.
    expected_output:
        - The log was not the expected.
        - The length of the subgroups of the match is not equal.
        - The values of the logs doesn't match.
    tags:
        - api
        - logs
        - logging
    '''
    wazuh_log_monitor = FileMonitor(API_LOG_FILE_PATH)
    json_log_monitor = FileMonitor(API_JSON_LOG_FILE_PATH)

    current_formats = get_configuration['configuration']['logs']['format'].split(',')

    send_request()

    expected_error =  'expected_error' in get_configuration
    if 'json' in current_formats:
        callback = callback_json_log_error if expected_error else callback_json_log_login_info
        json_result = json_log_monitor.start(timeout=API_GLOBAL_TIMEOUT, callback=callback,
                                             error_message='The log was not the expected.').result()
    if 'plain' in current_formats:
        callback = callback_plain_error if expected_error else callback_plain_log_login_info
        plain_result = wazuh_log_monitor.start(timeout=API_GLOBAL_TIMEOUT, callback=callback,
                                               error_message='The log was not the expected.').result()
    if len(current_formats) == 2:
        assert len(json_result.groups()) == len(plain_result.groups()), 'The length of the subgroups of the match is ' \
                                                                        'not equal.' \
                                                                        'Subgroups of the JSON match:' \
                                                                        f' {len(json_result.groups())}\n' \
                                                                        'Subgroups of the Plain match:' \

        for i in range(len(json_result.groups())):
            assert json_result.group(i + 1) == plain_result.group(i + 1), 'The values of the logs doesn\'t match.' \
                                                                      f'JSON log values: {json_result.groups()}\n' \
                                                                      f'Plain log values: {plain_result.groups()}\n'
