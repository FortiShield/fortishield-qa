import os
import pytest
from tempfile import gettempdir

import fortishield_testing as fw
from fortishield_testing.tools import configuration as config
from fortishield_testing import event_monitor as evm


# Test cases data
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_file_path = os.path.join(test_data_path, 'test_cases', 'cases_firewall_alerts.yaml')
alerts_json = os.path.join(gettempdir(), 'alerts.json')

# Playbooks
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']

# Configuration
configurations, configuration_metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)


@pytest.mark.parametrize('metadata', configuration_metadata, ids=cases_ids)
def test_firewall_alerts(configure_environment, metadata, generate_events):
    '''
    description: Check that an alert is generated when the firewall is disabled.

    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
            - Change status to the Windows firewall.
            - Insert log into a monitorized file
        - test:
            - Check in the alerts.json that an alerts of firewall disabled are generated when the firewall is disabled.
            - Check in the alerts.json that no alerts of firewall enabled are generated when the firewall is enabled.
        - teardown:
            - Restore initial configuration, ossec.conf.

    fortishield_min_version: 4.6.0

    tier: 0

    parameters:
        - configurate_environment:
            type: fixture
            brief: Set the fortishield configuration according to the configuration playbook.
        - metadata:
            type: dict
            brief: Fortishield configuration metadata.
        - generate_events:
            type: fixture
            brief: Generate RDP attack to the agent and copy the ossec.log and active-responses.log file to a specific
                   local folder to be analyzed.

    assertions:
        - Verify that the logs have been generated.

    input_description:
        - The `configuration.yaml` file provides the module configuration for this test.
        - The `generate_events.yaml` file provides the function to copy the log file to a temporary folder, provides
          the playbook to insert the log into the test files and, enable/disable the firewall.
    '''
    status = metadata['extra_vars']['firewall_status']
    for expected_log in metadata['extra_vars']['firewall_status_logs']:
        if 'disabled' in status:
            # When the firewall is inactive the alerts.json contains messages about firewall inactive status.
            evm.check_event(callback=expected_log, file_to_monitor=alerts_json, timeout=fw.T_5,
                            error_message=f"Could not find the event '{expected_log}' in alerts.json file")
        else:
            # When the firewall is active the alerts.json file does not contain any message about firewall status.
            with pytest.raises(TimeoutError):
                evm.check_event(callback=expected_log, file_to_monitor=alerts_json, timeout=fw.T_5,
                                error_message=f"Could not find the event '{expected_log}' in alerts.json file")
                raise AttributeError(f"The alert '{expected_log}' was generated unexpectedly")
