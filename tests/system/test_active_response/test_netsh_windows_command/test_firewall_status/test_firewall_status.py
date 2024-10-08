import os
import pytest
from tempfile import gettempdir

import fortishield_testing as fw
from fortishield_testing.tools import configuration as config
from fortishield_testing import event_monitor as evm


# Test cases data
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_file_path = os.path.join(test_data_path, 'test_cases', 'cases_firewall_status.yaml')
active_responses_log = os.path.join(gettempdir(), 'test_firewall_status', 'active-responses.log')

# Playbooks
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']

# Configuration
configurations, configuration_metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)


@pytest.mark.parametrize('metadata', configuration_metadata, ids=cases_ids)
def test_firewall_status(metadata, configure_environment, generate_events):
    '''
    description: Check that active-response detect that the firewall is disabled/enabled when and hydra attack is
                 performed.

    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
            - Change status to the Windows firewall.
            - Generate an RDP attack to the Windows agent
        - test:
            - Check in the active-responses.log that a log for firewall disabled is generated when the firewall is
              disabled.
            - Check in the active-responses.log that no log for firewall enabled is generated when the firewall is
              enabled.
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
            brief: Generate RDP attack to the agent and copy the active-responses.log file to a specific local folder
                   to be analyzed.

    assertions:
        - Verify that the logs have been generated.

    input_description:
        - The `configuration.yaml` file provides the module configuration for this test.
        - The `generate_events.yaml` file provides the function to copy the log file to a temporary folder and
          provides the playbook to generate the RDP attack.
    '''
    status = metadata['extra_vars']['firewall_status']
    for expected_log in metadata['extra_vars']['firewall_status_logs']:
        if 'disabled' in status:
            # When the firewall is inactive the alerts.json contains messages about firewall inactive status.
            evm.check_event(callback=expected_log, file_to_monitor=active_responses_log, timeout=fw.T_5,
                            error_message=f"Could not find the event '{expected_log}' in active-responses.log file")
        else:
            # When the firewall is active the alerts.json file does not contain any message about firewall status.
            with pytest.raises(TimeoutError):
                evm.check_event(callback=expected_log, file_to_monitor=active_responses_log, timeout=fw.T_5,
                                error_message=f"Could not find the event '{expected_log}' in active-responses.log file")
                raise AttributeError(f"The log '{expected_log}' was generated unexpectedly")
