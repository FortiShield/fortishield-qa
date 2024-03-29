'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.
           Created by Fortishield, Inc. <security@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
type: system
brief: This tests check that when a cluster has a series of agents with groups assigned, when an agent has it's
        group changed by a Fortishield-DB command, the cluster updates it's information.
tier: 2
modules:
    - cluster
components:
    - manager
    - agent
daemons:
    - fortishield-db
    - fortishield-clusterd
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
    - https://fortishield.github.io/documentation/current/user-manual/reference/tools/agent-auth.html
    - https://fortishield.github.io/documentation/current/user-manual/registering/command-line-registration.html
    - https://fortishield.github.io/documentation/current/user-manual/registering/agent-enrollment.html
tags:
    - fortishield-db
'''
import os
import time

import pytest
from fortishield_testing.tools import FORTISHIELD_PATH
from fortishield_testing.tools.system import HostManager
from system import create_new_agent_group, check_agent_groups
from system.test_cluster.test_agent_groups.common import register_agent


pytestmark = [pytest.mark.cluster, pytest.mark.big_cluster_40_agents_env]

# Hosts
test_infra_managers = ["fortishield-master", "fortishield-worker1", "fortishield-worker2"]
agents_in_cluster = 40
test_infra_agents = []
agent_groups = []
for x in range(agents_in_cluster):
    test_infra_agents.append("fortishield-agent" + str(x+1))
    agent_groups.append("Group" + str(x+1))

inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                              'provisioning', 'big_cluster_40_agents', 'inventory.yml')
host_manager = HostManager(inventory_path)
local_path = os.path.dirname(os.path.abspath(__file__))
test_time = 800
sync_delay = 40


# Tests
@pytest.mark.parametrize("agent_host", test_infra_managers[0:2])
def test_agent_groups_sync_time(agent_host, clean_environment):
    '''
    description: Check that after a long time when the manager has been unable to synchronize de databases, because
    new agents are being continually added, database synchronization is forced and the expected information is in
    all nodes after the expected sync time.
    fortishield_min_version: 4.4.0
    parameters:
        - agent_host:
            type: List
            brief: Name of the host where the agent will register en each case.
        - clean_enviroment:
            type: Fixture
            brief: Reset the fortishield log files at the start of the test. Remove all registered agents from master.
    assertions:
        - Verify that after registering and after starting the agent, the indicated group is synchronized.
    expected_output:
        - The 'Agent_name' with ID 'Agent_id' belongs to groups: 'group_name'.
    '''
    # Create all groups
    for group in agent_groups:
        create_new_agent_group(test_infra_managers[0], group, host_manager)

    # Register agents with their groups in manager
    agent_data = []
    for index, agent in enumerate(test_infra_agents):
        data = register_agent(agent, agent_host, host_manager, agent_groups[index])
        agent_data.append(data)

    # get the time before all the process is started
    time_before = time.time()
    end_time = time_before + test_time
    active_agent = 0
    while time.time() < end_time:
        if active_agent < agents_in_cluster:
            host_manager.run_command(test_infra_agents[active_agent], f'{FORTISHIELD_PATH}/bin/fortishield-control start')
            active_agent = active_agent + 1

    assert active_agent == agents_in_cluster, f"Unable to restart all agents in the expected time. \
                                                Agents restarted: {active_agent}"

    time.sleep(sync_delay)

    # Check that agent has the expected group assigned in all nodes
    for index, agent in enumerate(agent_data):
        data = agent_data[index]
        check_agent_groups(data[1], agent_groups[index], test_infra_managers, host_manager)
