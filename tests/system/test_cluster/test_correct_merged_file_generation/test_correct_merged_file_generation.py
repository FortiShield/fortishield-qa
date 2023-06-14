'''
copyright: Copyright (C) 2015-2023, Wazuh Inc.
           Created by Wazuh, Inc. <info@wazuh.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
type: system
brief: Wazuh manager should be able to create merged.mg file in order to share files with group of agents.
       In order to do it, when new files are present in any directory in /var/ossec/share/,
       those files must be monitored and to be taken in consideration by merged.mg
tier: 1, 2
modules:
    - enrollment
components:
    - manager
    - agent
daemons:
    - wazuh-authd
    - wazuh-agentd
os_platform:
    - linux
os_version:
    - Debian Buster
references:
    - https://documentation.wazuh.com/current/user-manual/reference/centralized-configuration.html
'''

import os
import pytest
import time
from wazuh_testing import T_1, T_10
from wazuh_testing.tools import WAZUH_PATH
from wazuh_testing.tools.file import read_yaml
from wazuh_testing.tools.monitoring import HostMonitor
from wazuh_testing.tools.system import HostManager
from wazuh_testing.tools.file import replace_regex_in_file
from system import (assign_agent_to_new_group, clean_cluster_logs, create_new_agent_group, delete_agent_group,
                    restart_cluster)

# pytestmark = [pytest.mark.cluster, pytest.mark.one_manager_agent_env]

agent_conf_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '..', 'provisioning', 'one_manager_agent', 'roles', 'agent-role', 'files', 'ossec.conf')
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              '..', 'provisioning', 'one_manager_agent', 'inventory.yaml')
host_manager = HostManager(inventory_path)
local_path = os.path.dirname(os.path.abspath(__file__))
messages_path = os.path.join(local_path, 'data/messages.yml')
test_cases_yaml = read_yaml(os.path.join(data_path, 'cases_correct_merged_file_generation.yaml'))
tmp_path = os.path.join(local_path, 'tmp')

reset_files = {
    'default': ['TestFile', 'TestFile2', 'EmptyFile', 'EmptyFile2', 'EmptyFile3', 'EmptyFile4', 'EmptyFile5',
                'EmptyFile6', 'EmptyFile7', 'EmptyFile8', 'EmptyFile9', 'EmptyFile10'],
    'TestGroup1': ['TestFileInTestGroup', 'TestFileInTestGroup2', 'EmptyFileInGroup', 'EmptyFileInGroup2',
                   'EmptyFileInGroup3', 'EmptyFileInGroup4', 'EmptyFileInGroup5', 'EmptyFileInGroup6',
                   'EmptyFileInGroup7', 'EmptyFileInGroup8', 'EmptyFileInGroup9', 'EmptyFileInGroup10']}
testinfra_hosts = ['wazuh-manager', 'wazuh-agent1']


@pytest.fixture()
def environment_setting(test_case):

    if test_case['metadata']['test_type'] == 'on_start':
        host_manager.run_command(testinfra_hosts[0], f'{WAZUH_PATH}/bin/wazuh-control stop')
    time.sleep(T_1)

    yield

    for file in reset_files['default']:
        host_manager.run_command(testinfra_hosts[0], f'rm {WAZUH_PATH}/etc/shared/default/{file}.txt -f')
    for file in reset_files['TestGroup1']:
        host_manager.run_command(testinfra_hosts[0], f'rm {WAZUH_PATH}/etc/shared/TestGroup1/{file}.txt -f')
    delete_agent_group(testinfra_hosts[0], 'TestGroup1', host_manager, 'api')
    host_manager.run_command(testinfra_hosts[0], f'rm -r {WAZUH_PATH}/etc/shared/TestGroup1 -f')
    create_new_agent_group(testinfra_hosts[0], 'TestGroup1', host_manager)
    assign_agent_to_new_group(testinfra_hosts[0], 'TestGroup1',
                              host_manager.run_command('wazuh-manager',
                                                       f'cut -c 1-3 {WAZUH_PATH}/etc/client.keys'), host_manager)
    clean_cluster_logs(testinfra_hosts, host_manager)


@pytest.mark.parametrize('test_case', [cases for cases in test_cases_yaml], ids=[cases['name']
                         for cases in test_cases_yaml])
def test_correct_merged_file_generation(test_case, environment_setting):
    '''
        description: Checking correct merged file generation.
        wazuh_min_version: 4.5.0
        parameters:
            - test_case:
                type: list
                brief: List of tests to be performed.
            - environment_setting:
                type: function
                brief: Clear files, directories and logs, reset initial conditions in /var/ossec/share
                        (includes agent enrollment).
                        Also stops the manager if it is required.
        assertions:
            - check merged.mg in the selected folder and the created file.
            - check if merged contains the correct information.
            - check if log contains the proper information in case the added file has no data.
        input_description: Different use cases are found in the test module and include parameters.
        expected_output:
            - merged.mg should be created and modified automatically considering the file/s and its/their information.
    '''
    # Declaring variables
    metadata = test_case['metadata']
    action = metadata['action']
    file_content = metadata['file_content']
    number_files = metadata['number_files']
    test_type = metadata['test_type']
    folder = metadata['shared_folder']
    file_name = metadata['file_name']
    files_list = []

    # Main action of the test
    if action == "remove":
        host_manager.run_command(testinfra_hosts[0], f'rm {WAZUH_PATH}/etc/shared/default/merged.mg -f')
    elif action == "add_files":
        if number_files == 1:
            host_manager.run_command(testinfra_hosts[0], f"touch {WAZUH_PATH}/etc/shared/{folder}/{file_name}.txt")
            if file_content != 'zero':
                host_manager.modify_file_content(host=testinfra_hosts[0],
                                                 path=f"{WAZUH_PATH}/etc/shared/{folder}/{file_name}.txt",
                                                 content=file_content)
        else:
            for number in range(number_files):
                files_list.append(f'{file_name}{number + 3}')
            for file in files_list:
                host_manager.run_command(testinfra_hosts[0], f"touch {WAZUH_PATH}/etc/shared/{folder}/{file}.txt")
                if file_content != 'zero':
                    host_manager.modify_file_content(host=testinfra_hosts[0],
                                                     path=f"{WAZUH_PATH}/etc/shared/{folder}/{file}.txt",
                                                     content=file_content)

    elif test_type == 'on_start' and action == 'remove':

        assert 'merged.mg' not in host_manager.run_command(testinfra_hosts[0],
                                                           f'ls {WAZUH_PATH}/etc/shared/default -la | grep merged')

    # Restart or wait
    if test_type == 'on_start':
        restart_cluster(testinfra_hosts, host_manager)
        time.sleep(T_1)
    if test_type == '10s':
        time.sleep(T_10)

    assert 'merged.mg' in host_manager.run_command(testinfra_hosts[0],
                                                   f"ls {WAZUH_PATH}/etc/shared/{folder} -la | grep merged")

    # Check number of files

    if file_name is not None:
        if number_files > 1:
            counter_files = 0
            for file in files_list:
                if file in host_manager.run_command(testinfra_hosts[0], f"ls {WAZUH_PATH}/etc/shared/{folder}"):
                    counter_files = counter_files + 1

            assert counter_files == number_files
        elif number_files == 1:
            assert file_name in host_manager.run_command(testinfra_hosts[0], f"ls {WAZUH_PATH}/etc/shared/{folder}")

    assert 'merged.mg' in host_manager.run_command(testinfra_hosts[0], f"ls {WAZUH_PATH}/etc/shared/{folder}")

    # Check content of merged.mg

    several_files_content_list = []
    if number_files > 1:
        merged_content = host_manager.run_command(testinfra_hosts[0], f"cat {WAZUH_PATH}/etc/shared/{folder}/merged.mg")
        for file in files_list:
            assert f'!0 {file}' in merged_content
    elif number_files == 1:
        if action == 'add_files':
            if file_content != 'zero':
                merged_value = f'!{len(file_content)} {file_name}.txt'
            else:
                merged_value = f'!0 {file_name}.txt'
        assert merged_value in host_manager.run_command(testinfra_hosts[0],
                                                        f"cat {WAZUH_PATH}/etc/shared/{folder}/merged.mg")

    # Check logs
    if file_content == 'zero':

        try:
            if number_files > 1:
                for file in files_list:
                    replace_regex_in_file(['FOLDER', 'FILENAME'], [folder, file], messages_path)
                    HostMonitor(inventory_path=inventory_path, messages_path=messages_path,
                                tmp_path=tmp_path).run(update_position=True)
            elif number_files == 1:
                replace_regex_in_file(['FOLDER', 'FILENAME'], [folder, file_name], messages_path)
                files_list.append(file_name)
                HostMonitor(inventory_path=inventory_path, messages_path=messages_path,
                            tmp_path=tmp_path).run(update_position=True)

        finally:
            replace_regex_in_file([folder, files_list[-1]], ['FOLDER', 'FILENAME'], messages_path)