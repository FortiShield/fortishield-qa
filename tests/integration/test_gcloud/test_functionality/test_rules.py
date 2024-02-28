'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <info@fortishield.github.io>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The Fortishield 'gcp-pubsub' module uses it to fetch different kinds of events
       (Data access, Admin activity, System events, DNS queries, etc.) from the
       Google Cloud infrastructure. Once events are collected, Fortishield processes
       them using its threat detection rules. Specifically, these tests will check
       if the module pulls messages that match the specified GCP rules and
       the generated alerts contain the expected rule ID.

components:
    - gcloud

suite: functionality

targets:
    - manager

daemons:
    - fortishield-analysisd
    - fortishield-monitord
    - fortishield-modulesd

os_platform:
    - linux

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - Ubuntu Focal
    - Ubuntu Bionic

references:
    - https://documentation.fortishield.github.io/current/user-manual/reference/ossec-conf/gcp-pubsub.html

tags:
    - rules
    - config
'''
import os
import sys

import pytest
from fortishield_testing import global_parameters
from fortishield_testing.fim import generate_params
from fortishield_testing.gcloud import callback_detect_gcp_alert, validate_gcp_event, publish_sync
from fortishield_testing.tools import LOG_FILE_PATH
from fortishield_testing.tools.configuration import load_fortishield_configurations
from fortishield_testing.tools.monitoring import FileMonitor
from fortishield_testing.tools.file import truncate_file

# Marks

pytestmark = [pytest.mark.tier(level=0), pytest.mark.server]

# variables

interval = '10s'
pull_on_start = 'no'
max_messages = 100
fortishield_log_monitor = FileMonitor(LOG_FILE_PATH)
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'fortishield_conf.yaml')
file_path = os.path.join(test_data_path, 'gcp_events.txt')
force_restart_after_restoring = False

# configurations

daemons_handler_configuration = {'daemons': ['fortishield-modulesd', 'fortishield-analysisd']}
monitoring_modes = ['scheduled']
conf_params = {'PROJECT_ID': global_parameters.gcp_project_id,
               'SUBSCRIPTION_NAME': global_parameters.gcp_subscription_name,
               'CREDENTIALS_FILE': global_parameters.gcp_credentials_file, 'INTERVAL': interval,
               'PULL_ON_START': pull_on_start, 'MAX_MESSAGES': max_messages,
               'MODULE_NAME': __name__}

p, m = generate_params(extra_params=conf_params,
                       modes=monitoring_modes)

configurations = load_fortishield_configurations(configurations_path, __name__, params=p, metadata=m)


# Preparing

truncate_file(LOG_FILE_PATH)


# fixtures

@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# tests

@pytest.mark.xfail(reason='Unstable, further information in fortishield/fortishield#17245')
@pytest.mark.skipif(sys.platform == "win32", reason="Windows does not have support for Google Cloud integration.")
def test_rules(get_configuration, configure_environment,
               daemons_handler_module, wait_for_gcp_start):
    '''
    description: Check if the 'gcp-pubsub' module gets messages matching the GCP rules. It also checks
                 if the triggered alerts contain the proper rule ID. For this purpose, the test will
                 publish multiple GCP messages and pull them later to generate alerts. Then, it
                 will verify that each alert triggered match the expected rule ID.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - restart_fortishield:
            type: fixture
            brief: Reset the 'ossec.log' file and start a new monitor.
        - wait_for_gcp_start:
            type: fixture
            brief: Wait for the 'gpc-pubsub' module to start.

    assertions:
        - Verify that the 'gcp-pubsub' module triggers an alert for each GCP event pulled.
        - Verify that the rule ID of the 'gcp-pubsub' alerts generated matches the expected one.

    input_description: A test case (ossec_conf) is contained in an external YAML file (fortishield_conf.yaml)
                       which includes configuration settings for the 'gcp-pubsub' module. The GCP events
                       used for testing are contained in the 'gcp_events.txt' file, and the GCP access
                       credentials can be found in the 'configuration_template.yaml' one.

    expected_output:
        - r'.*Sending gcp event: (.+)$'

    tags:
        - alerts
        - logs
        - rules
    '''
    str_interval = get_configuration['sections'][0]['elements'][4]['interval']['value']
    time_interval = int(''.join(filter(str.isdigit, str_interval)))
    rules_id = []
    file_ind = 0

    rules_id = [id for id in range(65005, 65011)]
    rules_id += [id for id in range(65012, 65039)]
    rules_id += [id for id in range(65041, 65047)]

    events_file = open(file_path, 'r')
    for line in events_file:
        # Publish messages to pull them later
        publish_sync(global_parameters.gcp_project_id, global_parameters.gcp_topic_name,
                     global_parameters.gcp_credentials_file, [line.strip()])
        event = fortishield_log_monitor.start(timeout=global_parameters.default_timeout + time_interval + 100,
                                        callback=callback_detect_gcp_alert,
                                        accum_results=1,
                                        error_message='Did not receive expected '
                                                      'Sending gcp event').result()
        validate_gcp_event(event)
        assert int(event['rule']['id']) == rules_id[file_ind]
        file_ind += 1
    events_file.close()
