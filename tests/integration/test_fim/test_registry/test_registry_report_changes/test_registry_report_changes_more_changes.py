'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: File Integrity Monitoring (FIM) system watches selected files and triggering alerts when
       these files are modified. Specifically, these tests will verify that FIM events include
       the 'content_changes' field with the tag 'More changes' when it exceeds the maximum size
       allowed, and the 'report_changes' option is enabled.
       The FIM capability is managed by the 'fortishield-syscheckd' daemon, which checks configured
       files for changes to the checksums, permissions, and ownership.

components:
    - fim

suite: registry_report_changes

targets:
    - agent

daemons:
    - fortishield-syscheckd

os_platform:
    - windows

os_version:
    - Windows 10
    - Windows 8
    - Windows 7
    - Windows Server 2019
    - Windows Server 2016
    - Windows Server 2012
    - Windows Server 2003
    - Windows XP

references:
    - https://fortishield.github.io/documentation/current/user-manual/capabilities/file-integrity/index.html
    - https://fortishield.github.io/documentation/current/user-manual/reference/ossec-conf/syscheck.html#diff

pytest_args:
    - fim_mode:
        realtime: Enable real-time monitoring on Linux (using the 'inotify' system calls) and Windows systems.
        whodata: Implies real-time monitoring but adding the 'who-data' information.
    - tier:
        0: Only level 0 tests are performed, they check basic functionalities and are quick to perform.
        1: Only level 1 tests are performed, they check functionalities of medium complexity.
        2: Only level 2 tests are performed, they check advanced functionalities and are slow to perform.

tags:
    - fim_registry_report_changes
'''
import os
import sys

import pytest
from test_fim.common import generate_string
from fortishield_testing import global_parameters
from fortishield_testing.fim import LOG_FILE_PATH, calculate_registry_diff_paths, registry_value_cud, KEY_WOW64_32KEY, \
    KEY_WOW64_64KEY, generate_params
from fortishield_testing.tools.configuration import load_fortishield_configurations, check_apply_test
from fortishield_testing.tools.monitoring import FileMonitor

MAX_STR_MORE_CHANGES = 59391
MORE_CHANGES_STR = "More changes..."
# Marks

pytestmark = [pytest.mark.win32, pytest.mark.tier(level=1)]

# Variables

key = "HKEY_LOCAL_MACHINE"
sub_key_1 = "SOFTWARE\\test_key"
sub_key_2 = "SOFTWARE\\Classes\\test_key"

test_regs = [os.path.join(key, sub_key_1),
             os.path.join(key, sub_key_2)]

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)
reg1, reg2 = test_regs

# Configurations

conf_params = {'WINDOWS_REGISTRY_1': reg1,
               'WINDOWS_REGISTRY_2': reg2}

configurations_path = os.path.join(test_data_path, 'fortishield_registry_report_changes.yaml')
p, m = generate_params(extra_params=conf_params, modes=['scheduled'])

configurations = load_fortishield_configurations(configurations_path, __name__, params=p, metadata=m)


# Fixtures


@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.skipif(sys.platform=='win32', reason="Blocked by #4077.")
@pytest.mark.parametrize('key, subkey, arch, value_name, tags_to_apply', [
    (key, sub_key_1, KEY_WOW64_64KEY, "some_value", {'test_report_changes'}),
    (key, sub_key_1, KEY_WOW64_32KEY, "some_value", {'test_report_changes'}),
    (key, sub_key_2, KEY_WOW64_64KEY, "some_value", {'test_report_changes'})
])
def test_report_changes_more_changes(key, subkey, arch, value_name, tags_to_apply,
                                     get_configuration, configure_environment, restart_syscheckd,
                                     wait_for_fim_start):
    '''
    description: Check if the 'fortishield-syscheckd' daemon detects when the character limit is reached in
                 the value changes, showing the 'More changes' tag in the 'content_changes' field of
                 the generated FIM events. For this purpose, the test will monitor a key, add a testing
                 value and modify it, adding more characters than the allowed limit. Finally, the test
                 will verify that the 'diff' file has been created, and the FIM event generated contains
                 the 'More changes' tag in its 'content_changes' field.

    fortishield_min_version: 4.2.0

    tier: 1

    parameters:
        - key:
            type: str
            brief: Path of the registry root key (HKEY_* constants).
        - subkey:
            type: str
            brief: The registry key being monitored by syscheck.
        - arch:
            type: str
            brief: Architecture of the registry.
        - value_name:
            type: str
            brief: Name of the testing value that will be created
        - tags_to_apply:
            type: set
            brief: Run test if matches with a configuration identifier, skip otherwise.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - restart_syscheckd:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.
        - wait_for_fim_start:
            type: fixture
            brief: Wait for realtime start, whodata start, or end of initial FIM scan.

    assertions:
        - Verify that FIM adds a 'diff' file when modifying the corresponding value.
        - Verify that FIM events include the 'content_changes' field with the 'More changes' tag
          when the changes made on a value exceed the characters limit.

    input_description: A test case (test_report_changes) is contained in external YAML file
                       (fortishield_registry_report_changes.yaml) which includes configuration
                       settings for the 'fortishield-syscheckd' daemon. That is combined with
                       the testing registry keys to be monitored defined in this module.

    expected_output:
        - r'.*Sending FIM event: (.+)$' ('added', 'modified', and 'deleted' events)

    tags:
        - scheduled
        - time_travel
    '''
    check_apply_test(tags_to_apply, get_configuration['tags'])
    values = {value_name: generate_string(MAX_STR_MORE_CHANGES, '0')}
    error_str = 'Expected {} in event'.format(MORE_CHANGES_STR)

    def report_changes_validator(event):
        """Validate content_changes attribute exists in the event"""
        for value in values:
            _, diff_file = calculate_registry_diff_paths(key, subkey, arch, value)
            assert os.path.exists(diff_file), '{diff_file} does not exist'
            assert event['data'].get('content_changes')[-len(MORE_CHANGES_STR):] == MORE_CHANGES_STR, error_str

    registry_value_cud(key, subkey, fortishield_log_monitor, arch=arch, value_list=values,
                       time_travel=get_configuration['metadata']['fim_mode'] == 'scheduled',
                       min_timeout=global_parameters.default_timeout, triggers_event=True,
                       validators_after_update=[report_changes_validator])
