'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: end_to_end

brief: This test will verify that a Sysmon events are detected correctly. Sysmon monitors system activity as
       process creation and termination, network connection and file changes.

components:
    - logcollector

targets:
    - manager
    - agent

daemons:
    - fortishield-logcollector
    - fortishield-analysisd

os_platform:
    - linux
    - windows

os_version:
    - CentOS 8
    - Windows Server 2019

references:
    - https://github.com/fortishield/fortishield-automation/wiki/Fortishield-demo:-Execution-guide#emotet
    - https://fortishield.github.io/blog/learn-to-detect-threats-on-windows-by-monitoring-sysmon-events/
tags:
    - demo
    - sysmon
    - emotet
'''
import json
import os
import re
import pytest

import fortishield_testing as fw
from fortishield_testing import end_to_end as e2e
from fortishield_testing import event_monitor as evm
from fortishield_testing.tools import configuration as config
from fortishield_testing.modules import TIER0, WINDOWS


test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_file_path = os.path.join(test_data_path, 'test_cases', 'cases_emotet.yaml')
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']

# Configuration
configurations, configuration_metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)

# Marks
pytestmark = [TIER0, WINDOWS]


@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
@pytest.mark.parametrize('metadata', configuration_metadata, ids=cases_ids)
def test_emotet(configure_environment, metadata, get_indexer_credentials, get_manager_ip, generate_events,
                clean_alerts_index):
    '''
    description: Check that an alert is generated when Emotet malware is executed.

    test_phases:
        - Set a custom Fortishield configuration.
        - Execute Emotet malware to generate the event.
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
    regsvr32_alert = metadata['regsvr32']
    word_executing_script_alert = metadata['word_executing_script']
    expected_alerts = [regsvr32_alert, word_executing_script_alert]

    for alert in expected_alerts:
        rule_level = alert['rule.level']
        rule_id = alert['rule.id']
        rule_description = alert['rule.description']
        rule_groups = alert['extra']['groups']
        timestamp_regex = r'\d+-\d+-\d+T\d+:\d+:\d+\.\d+[+|-]\d+'

        expected_alert_json = fr'\{{"timestamp":"({timestamp_regex})",' \
                              fr'"rule"\:{{"level"\:{rule_level},' \
                              fr'"description"\:"{rule_description}","id"\:"{rule_id}".*' \
                              fr'"groups"\:\["{rule_groups}"\].*\}}'

        expected_indexed_alert = fr'.*"rule":.*"level": {rule_level}, "description": "{rule_description}".*'\
                                 fr'"groups": \["{rule_groups}"\].*"id": "{rule_id}".*' \
                                 fr'"timestamp": "({timestamp_regex})".*'

        # Check that alert has been raised and save timestamp
        raised_alert = evm.check_event(callback=expected_alert_json, file_to_monitor=e2e.fetched_alerts_json_path,
                                       timeout=fw.T_5, error_message=f"The alert '{rule_description}'"
                                                                     ' has not occurred').result()
        raised_alert_timestamp = raised_alert.group(1)

        query = e2e.make_query([
            {
                "term": {
                    "rule.id": f"{rule_id}"
                }
            },
            {
                "term": {
                    "timestamp": f"{raised_alert_timestamp}"
                }
            }
        ])

        # Check if the alert has been indexed and get its data
        response = e2e.get_alert_indexer_api(query=query, credentials=get_indexer_credentials,
                                             ip_address=get_manager_ip)
        indexed_alert = json.dumps(response.json())

        # Check that the alert data is the expected one
        alert_data = re.search(expected_indexed_alert, indexed_alert)
        assert alert_data is not None, f"Alert '{rule_description}' triggered, but not indexed"
