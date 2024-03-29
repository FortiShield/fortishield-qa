'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.
           Created by Fortishield, Inc. <security@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: Fortishield-db is the daemon in charge of the databases with all the Fortishield persistent information, exposing a socket
       to receive requests and provide information. Fortishield-db has the capability to do automatic database backups, based
       on the configuration parameters. This test, checks the proper working of the backup configuration and the
       backup files are generated correctly.

tier: 0

modules:
    - fortishield_db

components:
    - manager

daemons:
    - fortishield-db

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
    - https://fortishield.github.io/documentation/current/user-manual/reference/daemons/fortishield-db.html

tags:
    - fortishield_db
'''
import os
import subprocess

import pytest
import time
import numbers

from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.services import restart_fortishield_function
from fortishield_testing.tools.monitoring import FileMonitor, generate_monitoring_callback
from fortishield_testing.tools import LOG_FILE_PATH, FORTISHIELD_PATH
from fortishield_testing.tools.utils import validate_interval_format
from fortishield_testing.modules import TIER0, LINUX, SERVER


# Marks
pytestmark =  [TIER0, LINUX, SERVER]


# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_db_backups_conf.yaml')
backups_path = os.path.join(FORTISHIELD_PATH, 'backup', 'db')
interval = 5

parameters = [{'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':''},
              {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':'value'},
              {'ENABLED': 'yes', 'INTERVAL': '', 'MAX_FILES':'1'},
              {'ENABLED': 'yes', 'INTERVAL': 'value', 'MAX_FILES':1},
              {'ENABLED': 'no', 'INTERVAL': str(interval)+'s', 'MAX_FILES':1},
              {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':1},
              {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':3},
              {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':0}
            ]

metadata = [{'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':''},
            {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':'value'},
            {'ENABLED': 'yes', 'INTERVAL': '', 'MAX_FILES':1},
            {'ENABLED': 'yes', 'INTERVAL': 'value', 'MAX_FILES':1},
            {'ENABLED': 'no', 'INTERVAL': str(interval)+'s', 'MAX_FILES':1},
            {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':1},
            {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':3},
            {'ENABLED': 'yes', 'INTERVAL': str(interval)+'s', 'MAX_FILES':0}
           ]

configurations = load_fortishield_configurations(configurations_path, __name__ ,
                                           params=parameters, metadata=metadata)


# Variables
BACKUP_CREATION_CALLBACK = r'.*Created Global database backup "(backup/db/global.db-backup.*.gz)"'
WRONG_INTERVAL_CALLBACK = r".*Invalid value for element ('interval':.*)"
WRONG_MAX_FILES_CALLBACK = r".*Invalid value for element ('max_files':.*)"
fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)
timeout = 15


# Fixtures
@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# Tests
@pytest.mark.parametrize('backups_path', [backups_path])
def test_wdb_backup_configs(get_configuration, configure_environment, clear_logs, remove_backups, backups_path):
    '''
    description: Check that given different wdb backup configuration parameters, the expected behavior is achieved.
                 For this, the test gets a series of parameters for the fortishield_db_backups_conf.yaml file and applies
                 them to the manager's ossec.conf. It checks in case of erroneous configurations that the manager was
                 unable to start; otherwise it will check that after creating "max_files+1", there are a total of 
                 "max_files" backup files in the backup folder.

    fortishield_min_version: 4.4.0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_enviroment:
            type: fixture
            brief: Configure a custom environment for testing.
        - clear_logs:
            type: fixture
            brief: Clears the ossec.log file and starts a new File_Monitor.
        - remove_backups:
            type: fixture
            brief: Creates the folder where the backups will be stored in case it doesn't exist. It clears it when the
                   test yields.
    assertions:
        - Verify that manager starts behavior is correct for any given configuration.
        - Verify that the backup file has been created, wait for "max_files+1".
        - Verify that after "max_files+1" files created, there's only "max_files" in the folder.

    input_description:
        - Test cases are defined in the parameters and metada variables, that will be applied to the the 
          fortishield_db_backup_command.yaml file. The parameters tested are: "enabled", "interval" and "max_files".
          With the given input the test will check the correct behavior of wdb automatic global db backups.

    expected_output:
        - f"Invalid value element for interval..."
        - f"Invalid value element for max_files..."
        - f'Did not receive expected "Created Global database..." event'
        - f'Expected {test_max_files} backup creation messages, but got {result}'
        - f'Wrong backup file ammount, expected {test_max_files} but {total_files} are present in folder.

    tags:
        - fortishield_db
        - wdb_socket

    '''
    test_interval = get_configuration['metadata']['INTERVAL']
    test_max_files = get_configuration['metadata']['MAX_FILES']
    try:
        restart_fortishield_function()
    except (subprocess.CalledProcessError, ValueError) as err:
        if not validate_interval_format(test_interval):
            fortishield_log_monitor.start(callback=generate_monitoring_callback(WRONG_INTERVAL_CALLBACK), timeout=timeout,
                                           error_message='Did not receive expected '
                                                         '"Invalid value element for interval..." event')
            return
        elif not isinstance(test_max_files, numbers.Number) or test_max_files==0:
            fortishield_log_monitor.start(callback=generate_monitoring_callback(WRONG_MAX_FILES_CALLBACK), timeout=timeout,
                                           error_message='Did not receive expected '
                                                         '"Invalid value element for max_files..." event')
            return
        else:
            pytest.fail(f"Got unexpected Error: {err}")

    # Wait for backup files to be generated
    time.sleep(interval*(int(test_max_files)+1))

    # Manage if backup generation is not enabled - no backups expected
    if get_configuration['metadata']['ENABLED'] == 'no':
        # Fail the test if a file or more were found in the backups_path
        if os.listdir(backups_path):
            pytest.fail("Error: A file was found in backups_path. No backups where expected when enabled is 'no'.")
    # Manage if backup generation is enabled - one or more backups expected
    else:
        result= fortishield_log_monitor.start(timeout=timeout, accum_results=test_max_files+1,
                                        callback=generate_monitoring_callback(BACKUP_CREATION_CALLBACK),
                                        error_message=f'Did not receive expected\
                                                        "Created Global database..." event').result()
        assert len(result) == test_max_files+1, f'Expected {test_max_files} backup creation messages, but got {result}.'
        total_files=0
        for file in os.listdir(backups_path):
            total_files = total_files+1
        assert total_files == test_max_files, f'Wrong backup file ammount, expected {test_max_files} \
                                                but {total_files} are present in folder.'
