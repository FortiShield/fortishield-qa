'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.

           Created by Fortishield, Inc. <security@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'fortishield-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector starts to monitor log files when
       the 'query' tag is set in the configuration.
       Log data collection is the real-time process of making sense out of the records generated by
       servers or devices. This component can receive logs through text files or Windows event logs.
       It can also directly receive logs via remote syslog which is useful for firewalls and
       other such devices.

components:
    - logcollector

suite: configuration

targets:
    - agent

daemons:
    - fortishield-logcollector

os_platform:
    - macos
    - windows

os_version:
    - macOS Catalina
    - macOS Server
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://fortishield.github.io/documentation/current/user-manual/capabilities/log-data-collection/index.html
    - https://fortishield.github.io/documentation/current/user-manual/reference/ossec-conf/localfile.html#query

tags:
    - logcollector_configuration
'''
import os
import pytest
import fortishield_testing.logcollector as logcollector
from fortishield_testing.tools.configuration import load_fortishield_configurations
import sys
from fortishield_testing.tools.utils import lower_case_key_dictionary_array

# Marks
query_list = ['']
parameters = []

level_list = ['default', 'info', 'debug']
type_list = ['log', 'trace', 'activity', 'log,trace', 'activity,log', 'activity,trace']
fortishield_configuration = 'fortishield_basic_configuration_query_macos.yaml'

if sys.platform != 'win32' and sys.platform != 'darwin':
    pytestmark = [pytest.mark.skip, pytest.mark.tier(level=0)]
else:
    pytestmark = [pytest.mark.tier(level=0)]
    if sys.platform == 'darwin':
        clauses = ['eventMessage', 'processImagePath', 'senderImagePath', 'subsystem', 'category']
        location = log_format = 'macos'
        for clause in clauses:
            query_list += [f'{clause} CONTAINS[c] "com.apple.geod"',
                           f'{clause} == "testing"',
                           f'{clause} <> "testing"',
                           f'{clause} = "testing"',
                           f'NOT {clause} CONTAINS[c] "testing" AND  {clause} LIKE "example"',
                           f'{clause} ENDSWITH[c] "testing" &&  {clause} MATCHES[c] "example"',
                           f'{clause} BEGINSWITH[c] "testing" OR  {clause} IN "example"'
                           ]
    else:
        fortishield_configuration = 'fortishield_basic_configuration_query_windows.yaml'
        location = ['Security', 'System', 'Application']
        log_format = 'eventchannel'
        query_list += ['Event[System/EventID = 4624]',
                       'Event[System/EventID = 1343 and (EventData/Data[@Name=\'LogonType\'] = 2',
                       'Event[System/EventID = 6632 and (EventData/Data[@Name=\'LogonType\'] = 93 or '
                       'EventData/Data[@Name=\'LogonType\'] = 111)]',
                       'Event[EventData[Data[@Name="property"]="value"]]',
                       'Event[EventData[Data="value"]]',
                       'Event[ EventData[Data[@Name="PropA"]="ValueA" and  Data[@Name="PropB"]="ValueB" ]]'
                       ]

    for query in query_list:
        if isinstance(location, list):
            for channel in location:
                parameters += [{'LOCATION': channel, 'LOG_FORMAT': log_format, 'QUERY': query}]
        else:
            for level in level_list:
                for type in type_list:
                    parameters += [{'LOCATION': location, 'LOG_FORMAT': log_format,
                                    'QUERY': query, 'TYPE': type, 'LEVEL': level}]

metadata = lower_case_key_dictionary_array(parameters)

# Configuration
no_restart_windows_after_configuration_set = True
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, fortishield_configuration)
configurations = load_fortishield_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)

configuration_ids = [f"{x['location']}_{x['log_format']}_{x['query']}_{x['level']}_{x['type']}" + f"" if 'level' in x
                     else f"{x['location']}_{x['log_format']}_{x['query']}" for x in metadata]


@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.skip("This test needs refactor/fixes. Has flaky behaviour. Skipped by Issue #3218")
def test_configuration_query_valid(get_configuration, configure_environment, restart_logcollector):
    '''
    description: Check if the 'fortishield-logcollector' daemon starts properly when the 'query' tag is used.
                 For this purpose, the test will configure the logcollector to monitor a testing log using
                 the query tag. That query will be different depending on the system OS. Finally, the test
                 will verify that the logcollector is started by verifying that the 'monitoring' or 'analyzing'
                 events are generated.

    fortishield_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - restart_logcollector:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.

    assertions:
        - Verify that the logcollector can start to monitor log files when the 'query' tag is used.

    input_description: A configuration template (test_basic_configuration_query_macos and
                       test_basic_configuration_query_windows) are contained in external YAML files
                       (fortishield_basic_configuration_query_macos.yaml and fortishield_basic_configuration_query_windows.yaml).
                       Those templates are combined with different test cases defined in the module. Those include
                       configuration settings for the 'fortishield-logcollector' daemon.

    expected_output:
        - r'Monitoring macOS logs with'
        - r'Analyzing event log.*'

    tags:
        - invalid_settings
        - logs
    '''
    configuration = get_configuration['metadata']
    log_format = configuration['log_format']

    if log_format == 'macos':
        log_callback = logcollector.callback_monitoring_macos_logs()
        fortishield_log_monitor.start(timeout=5, callback=log_callback,
                                error_message=logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_EVENTCHANNEL)
    else:
        log_callback = logcollector.callback_eventchannel_analyzing(configuration['location'])
        fortishield_log_monitor.start(timeout=5, callback=log_callback,
                                error_message=logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_EVENTCHANNEL)
