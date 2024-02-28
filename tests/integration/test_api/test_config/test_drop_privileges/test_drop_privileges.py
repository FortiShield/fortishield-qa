'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: These tests will check if the 'drop_privileges' setting of the API is working properly.
       This setting allows the user who starts the 'fortishield-apid' daemon to be different from
       the 'root' user. The Fortishield API is an open source 'RESTful' API that allows for interaction
       with the Fortishield manager from a web browser, command line tool like 'cURL' or any script
       or program that can make web requests.

components:
    - api

suite: config

targets:
    - manager

daemons:
    - fortishield-apid
    - fortishield-analysisd
    - fortishield-syscheckd
    - fortishield-db

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
    - https://fortishield.github.io/documentation/current/user-manual/api/getting-started.html
    - https://fortishield.github.io/documentation/current/user-manual/api/configuration.html#drop-privileges

tags:
    - api
'''
import os
import pwd

import pytest
from fortishield_testing.tools.configuration import check_apply_test, get_api_conf
from fortishield_testing.tools.services import get_process_cmd

# Marks

pytestmark = pytest.mark.server

# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'conf.yaml')
configuration = get_api_conf(configurations_path)


# Fixtures

@pytest.fixture(scope='module', params=configuration)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# Tests

@pytest.mark.parametrize('tags_to_apply', [
    {'drop_privileges_enabled'},
    {'drop_privileges_disabled'},
])
def test_drop_privileges(tags_to_apply, get_configuration, configure_api_environment,
                         restart_api, wait_for_start, get_api_details):
    '''
    description: Check if 'drop_privileges' affects the user of the API process.
                 In this test, the 'PID' of the API process is obtained. After that,
                 it gets the user ('root' or 'fortishield') and checks if it matches the
                 'drop_privileges' setting.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - tags_to_apply:
            type: set
            brief: Run test if match with a configuration identifier, skip otherwise.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_api_environment:
            type: fixture
            brief: Configure a custom environment for API testing.
        - restart_api:
            type: fixture
            brief: Reset 'api.log' and start a new monitor.
        - wait_for_start:
            type: fixture
            brief: Wait until the API starts.
        - get_api_details:
            type: fixture
            brief: Get API information.

    assertions:
        - Verify that when 'drop_privileges' is enabled the user who has started the 'fortishield-apid' daemon is 'fortishield'.
        - Verify that when 'drop_privileges' is disabled the user who has started the 'fortishield-apid' daemon is 'root'.

    input_description: Different test cases are contained in an external YAML file (conf.yaml)
                       which includes API configuration parameters.

    expected_output:
        - PID of the 'fortishield-apid' process.
        - r'fortishield' (if 'drop_privileges == yes')
        - r'root' (if 'drop_privileges == no')
    '''
    check_apply_test(tags_to_apply, get_configuration['tags'])
    drop_privileges = get_configuration['configuration']['drop_privileges']

    # Get fortishield-apid process info
    api_process = get_process_cmd('/api/scripts/fortishield-apid.py')
    if not api_process:
        pytest.fail("The process '/api/scripts/fortishield-apid.py' could not be found")

    # Get current user of the process
    proc_stat_file = os.stat("/proc/%d" % api_process.pid)
    uid = proc_stat_file.st_uid
    username = pwd.getpwuid(uid)[0]

    if drop_privileges:
        assert username == 'fortishield', f'Expected user was "fortishield", but the real one is {username}'
    else:
        assert username == 'root', f'Expected user was "root", but the real one is {username}'
