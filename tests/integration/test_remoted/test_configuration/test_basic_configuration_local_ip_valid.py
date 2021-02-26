# Copyright (C) 2015-2021, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import os
import pytest
import netifaces

import wazuh_testing.api as api

import wazuh_testing.remote as remote
from wazuh_testing.tools.configuration import load_wazuh_configurations

# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'wazuh_basic_configuration.yaml')

parameters = []
metadata = []

# Get all network interfaces ips using netifaces
array_interfaces_ip = []
network_interfaces = netifaces.interfaces()

for interface in network_interfaces:
    ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
    array_interfaces_ip.append(ip)

for local_ip in array_interfaces_ip:
    parameters.append({'LOCAL_IP': local_ip})
    metadata.append({'local_ip': local_ip})

configurations = load_wazuh_configurations(configurations_path, "test_basic_configuration_local_ip", params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['LOCAL_IP']}" for x in parameters]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_local_ip_valid(get_configuration, configure_environment, restart_remoted):
    """

    """

    cfg = get_configuration['metadata']

    # Check that API query return the selected configuration
    for field in cfg.keys():
        api_answer = api.get_manager_configuration(section="remote", field=field)
        assert cfg[field] == api_answer, "Wazuh API answer different from introduced configuration"
