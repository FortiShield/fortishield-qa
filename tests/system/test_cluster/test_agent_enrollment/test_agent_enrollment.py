# Copyright (C) 2015-2022, Fortishield Inc.
# Created by Fortishield, Inc. <info@fortishield.github.io>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import os

import pytest
from fortishield_testing.tools import FORTISHIELD_PATH, FORTISHIELD_LOGS_PATH
from fortishield_testing.tools.system_monitoring import HostMonitor
from fortishield_testing.tools.system import HostManager


pytestmark = [pytest.mark.cluster, pytest.mark.enrollment_cluster_env]

# Hosts
testinfra_hosts = ["fortishield-master", "fortishield-worker1", "fortishield-agent1"]

inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                              'provisioning', 'enrollment_cluster', 'inventory.yml')
host_manager = HostManager(inventory_path)
local_path = os.path.dirname(os.path.abspath(__file__))
messages_path = os.path.join(local_path, 'data/messages.yml')
tmp_path = os.path.join(local_path, 'tmp')


# Remove the agent once the test has finished
@pytest.fixture(scope='module')
def clean_environment():
    yield
    agent_id = host_manager.run_command('fortishield-master', f'cut -c 1-3 {FORTISHIELD_PATH}/etc/client.keys')
    host_manager.get_host('fortishield-master').ansible("command", f'{FORTISHIELD_PATH}/bin/manage_agents -r {agent_id}',
                                                  check=False)
    host_manager.control_service(host='fortishield-agent1', service='fortishield', state="stopped")
    host_manager.clear_file(host='fortishield-agent1', file_path=os.path.join(FORTISHIELD_PATH, 'etc', 'client.keys'))
    host_manager.clear_file(host='fortishield-agent1', file_path=os.path.join(FORTISHIELD_LOGS_PATH, 'ossec.log'))


def test_agent_enrollment(clean_environment):
    """Check agent enrollment process works as expected. An agent pointing to a worker should be able to register itself
    into the master by starting Fortishield-agent process."""
    # Clean ossec.log and cluster.log
    host_manager.clear_file(host='fortishield-master', file_path=os.path.join(FORTISHIELD_LOGS_PATH, 'ossec.log'))
    host_manager.clear_file(host='fortishield-worker1', file_path=os.path.join(FORTISHIELD_LOGS_PATH, 'ossec.log'))
    host_manager.clear_file(host='fortishield-master', file_path=os.path.join(FORTISHIELD_LOGS_PATH, 'cluster.log'))
    host_manager.clear_file(host='fortishield-worker1', file_path=os.path.join(FORTISHIELD_LOGS_PATH, 'cluster.log'))

    # Start the agent enrollment process by restarting the fortishield-agent
    host_manager.control_service(host='fortishield-master', service='fortishield', state="restarted")
    host_manager.control_service(host='fortishield-worker1', service='fortishield', state="restarted")
    host_manager.get_host('fortishield-agent1').ansible('command', f'service fortishield-agent restart', check=False)

    # Run the callback checks for the ossec.log and the cluster.log
    HostMonitor(inventory_path=inventory_path,
                messages_path=messages_path,
                tmp_path=tmp_path).run()

    # Make sure the worker's client.keys is not empty
    assert host_manager.get_file_content('fortishield-worker1', os.path.join(FORTISHIELD_PATH, 'etc', 'client.keys'))

    # Make sure the agent's client.keys is not empty
    assert host_manager.get_file_content('fortishield-agent1', os.path.join(FORTISHIELD_PATH, 'etc', 'client.keys'))

    # Check if the agent is active
    agent_id = host_manager.run_command('fortishield-master', f'cut -c 1-3 {FORTISHIELD_PATH}/etc/client.keys')
    assert host_manager.run_command('fortishield-master', f'{FORTISHIELD_PATH}/bin/agent_control -i {agent_id} | grep Active')
