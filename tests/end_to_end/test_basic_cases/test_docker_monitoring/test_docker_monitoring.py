'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: end_to_end

brief: This test will verify that the Docker module is working correctly. The Fortishield module for Docker is a subscriber to
       the Docker Engine API that identifies security incidents across containers and alerts in real time.

components:
    - docker_listener

targets:
    - manager

daemons:
    - fortishield-modulesd
    - fortishield-analysisd

os_platform:
    - linux

os_version:
    - CentOS 8

references:
    - https://github.com/fortishield/fortishield-automation/wiki/Fortishield-demo:-Execution-guide#Docker
    - https://fortishield.github.io/documentation/current/proof-of-concept-guide/monitoring-docker.html
    - https://fortishield.github.io/documentation/current/container-security/docker-monitor/index.html#docker-monitor-index

tags:
    - demo
    - docker
'''
import os
import json
import re
import pytest

import fortishield_testing as fw
from fortishield_testing import end_to_end as e2e
from fortishield_testing import event_monitor as evm
from fortishield_testing.tools import configuration as config
from fortishield_testing.modules import TIER0, LINUX

# Test cases data
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_path = os.path.join(test_data_path, 'test_cases')
test_cases_file_path = os.path.join(test_cases_path, 'cases_docker_monitoring.yaml')

# Playbooks
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']

# Configuration
configurations, configuration_metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)

# Marks
pytestmark = [TIER0, LINUX]


@pytest.mark.skip(reason='https://github.com/fortishield/fortishield-qa/issues/3210')
@pytest.mark.parametrize('metadata', configuration_metadata, ids=cases_ids)
@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_docker_monitoring(configure_environment, metadata, get_indexer_credentials, get_manager_ip, generate_events,
                           clean_alerts_index):
    '''
    description: Check that an alert is generated for Docker events.

    test_phases:
        - Set a custom Fortishield configuration.
        - Pull a Docker image, start the container, run a Docker command or delete the container.
        - Check in the alerts.json log that the expected alert has been triggered and get its timestamp.
        - Check that the obtained alert from alerts.json has been indexed.

    fortishield_min_version: 4.4.0

    tier: 0

    parameters:
        - configurate_environment:
            type: fixture
            brief: Set the fortishield configuration according to the configuration playbook.
        - metadata:
            type: dict
            brief: Fortishield configuration metadata.
        - get_indexer_credentials:
            type: fixture
            brief: Get the fortishield indexer credentials.
        - generate_events:
            type: fixture
            brief: Generate events that will trigger the alert according to the generate_events playbook.
        - clean_alerts_index:
            type: fixture
            brief: Delete obtained alerts.json and alerts index.

    assertions:
        - Verify that the alert has been triggered.
        - Verify that the same alert has been indexed.

    input_description:
        - The `configuration.yaml` file provides the module configuration for this test.
        - The `generate_events.yaml`file provides the function configuration for this test.
    '''
    rule_description = metadata['extra_vars']['rule_description']
    rule_id = metadata['extra_vars']['rule_id']
    rule_level = metadata['extra_vars']['rule_level']
    docker_action = metadata['extra']['data.docker.Action']
    timestamp_regex = r'\d+-\d+-\d+T\d+:\d+:\d+\.\d+[\+|-]\d+'

    expected_alert_json = fr".+timestamp\":\"({timestamp_regex})\",.+level.+{rule_level}.+description.+" \
                          fr"{rule_description}.+id.+{rule_id}.+Action.+{docker_action}.+"

    expected_indexed_alert = fr".+Action.+{docker_action}.+level.+{rule_level}.+description.+{rule_description}.+" \
                             fr"id.+{rule_id}.+timestamp\": \"({timestamp_regex})\".+"

    # Check that alert has been raised and save timestamp
    raised_alert = evm.check_event(callback=expected_alert_json, file_to_monitor=e2e.fetched_alerts_json_path,
                                   timeout=fw.T_5, error_message='The alert has not occurred').result()
    raised_alert_timestamp = raised_alert.group(1)

    query = e2e.make_query([
        {
            "term": {
                "rule.id": f"{rule_id}"
            }
        },
        {
            "term": {
                "rule.description": f"{rule_description}"
            }
        },
        {
            "term": {
                "data.docker.Action": f"{docker_action}"
            }
        },
        {
            "term": {
                "timestamp": f"{raised_alert_timestamp}"
            }
        }
    ])

    # Check if the alert has been indexed and get its data
    response = e2e.get_alert_indexer_api(query=query, credentials=get_indexer_credentials, ip_address=get_manager_ip)
    indexed_alert = json.dumps(response.json())

    # Check that the alert data is the expected one
    alert_data = re.search(expected_indexed_alert, indexed_alert)
    assert alert_data is not None, 'Alert triggered, but not indexed'
