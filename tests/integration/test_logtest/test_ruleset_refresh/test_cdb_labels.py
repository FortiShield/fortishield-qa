'''
copyright: Copyright (C) 2015-2021, Wazuh Inc.

           Created by Wazuh, Inc. <info@wazuh.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'wazuh-logtest' tool allows the testing and verification of rules and decoders against provided log examples
       remotely inside a sandbox in 'wazuh-analysisd'. This functionality is provided by the manager, whose work
       parameters are configured in the ossec.conf file in the XML rule_test section. Test logs can be evaluated through
       the 'wazuh-logtest' tool or by making requests via RESTful API. These tests will check if the logtest
       configuration is valid. Also checks rules, decoders, decoders, alerts matching logs correctly.

tier: 0

modules:
    - logtest

components:
    - manager

daemons:
    - wazuh-analysisd

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
    - https://documentation.wazuh.com/current/user-manual/reference/tools/wazuh-logtest.html
    - https://documentation.wazuh.com/current/user-manual/capabilities/wazuh-logtest/index.html
    - https://documentation.wazuh.com/current/user-manual/ruleset/testing.html?highlight=logtest
    - https://documentation.wazuh.com/current/user-manual/capabilities/wazuh-logtest/logtest-configuration.html
    - https://documentation.wazuh.com/current/user-manual/reference/daemons/wazuh-analysisd.html
    - https://documentation.wazuh.com/current/user-manual/ruleset/cdb-list.html

tags:
    - logtest_configuration
'''
import os
import pytest

from wazuh_testing.tools import WAZUH_PATH
from yaml import safe_load
from shutil import copy
from json import loads

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_path = os.path.join(test_data_path, 'cdb_list.yaml')

with open(messages_path) as f:
    test_cases = safe_load(f)

# Variables
logtest_path = os.path.join(os.path.join(WAZUH_PATH, 'queue', 'sockets', 'logtest'))
receiver_sockets_params = [(logtest_path, 'AF_UNIX', 'TCP')]
receiver_sockets = None


# Fixtures
@pytest.fixture(scope='function')
def configure_cdbs_list(get_configuration, request):
    """Configure a custom cdbs for testing.

    Restarting Wazuh is not needed for applying the configuration, it is optional.
    """

    # cdb configuration for testing
    cdb_dir = os.path.join(WAZUH_PATH, get_configuration['cdb_dir'])
    if not os.path.exists(cdb_dir):
        os.makedirs(cdb_dir)

    file_cdb_test = os.path.join(test_data_path, get_configuration['cdb_file'])
    file_cdb_dst = os.path.join(cdb_dir, get_configuration['cdb_file'])

    copy(file_cdb_test, file_cdb_dst)

    # rule configuration for testing
    rule_dir = os.path.join(WAZUH_PATH, get_configuration['rule_dir'])
    if not os.path.exists(rule_dir):
        os.makedirs(rule_dir)

    file_rule_test = os.path.join(test_data_path, get_configuration['rule_file'])
    file_rule_dst = os.path.join(rule_dir, get_configuration['rule_file'])

    copy(file_rule_test, file_rule_dst)

    yield

    # restore previous configuration
    os.remove(file_cdb_dst)
    if len(os.listdir(cdb_dir)) == 0:
        os.rmdir(cdb_dir)
    os.remove(file_rule_dst)
    if len(os.listdir(rule_dir)) == 0:
        os.rmdir(rule_dir)


@pytest.fixture(scope='module', params=test_cases, ids=[test_case['name'] for test_case in test_cases])
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_cdb_list(restart_required_logtest_daemons, get_configuration,
                  configure_environment, configure_cdbs_list,
                  wait_for_logtest_startup, connect_to_sockets_function):
    '''
    description: Checks if modifying the configuration of the cdb list, by using its labels, takes effect when opening
                 new logtest sessions without having to reset the manager. To do this, it sends a request to logtest
                 socket with the test case and it checks that the result matches with the test case result.

    wazuh_min_version: 4.2.0

    parameters:
        - restart_required_logtest_daemons:
            type: fixture
            brief: Wazuh logtests daemons handler.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing. Restart Wazuh is needed for applying the configuration.
        - configure_cdbs_list:
            type: fixture
            brief: Configure a custom cdbs for testing.
        - wait_for_logtest_startup:
            type: fixture
            brief: Wait until logtest has begun.
        - connect_to_sockets_function:
            type: fixture
            brief: Function scope version of 'connect_to_sockets' which connects to the specified sockets for the test.

    assertions:
        - Verify that the result does not contain errors.
        - Verify that the result is from the cdb list.
        - Verify that the 'rule_id' sent matches with the result.

    input_description: Some test cases are defined in the module. These include some input configurations stored in
                       the 'cdb_list.yaml'.

    expected_output:
        - result.error == 0
        - cdb not in result.data.output
        - result.data.output.rule.id == test_case.rule_id

    tags:
        - cdb
        - rules
        - analysisd
    '''
    # send the logtest request
    receiver_sockets[0].send(get_configuration['input'], size=True)

    # receive logtest reply and parse it
    response = receiver_sockets[0].receive(size=True).rstrip(b'\x00').decode()
    result = loads(response)

    assert result['error'] == 0
    if 'test_exclude' in get_configuration:
        assert 'cdb' not in result['data']['output']
    else:
        assert result['data']['output']['rule']['id'] == get_configuration['rule_id']