# Copyright (C) 2015-2020, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import os
import re
import json

from jsonschema import validate
from wazuh_testing.tools import WAZUH_PATH
from google.cloud import pubsub_v1

_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')


def validate_gcp_event(event):
    """
    Check if event is properly formatted according to some checks.

    Parameters
    ----------
    event : dict
        Represents an event generated by Google Cloud.
    """

    json_file = 'gcp_event.json'
    with open(os.path.join(_data_path, json_file), 'r') as f:
        schema = json.load(f)
    validate(schema=schema, instance=event)


def callback_detect_start_gcp(line):
    if 'wm_gcp_main(): INFO: Module started.' in line:
        return line
    return None


def callback_detect_start_fetching_logs(line):
    if 'wm_gcp_main(): DEBUG: Starting fetching of logs.' in line:
        return line
    return None


def callback_detect_start_gcp_sleep(line):
    match = re.match(r'.*wm_gcp_main\(\): DEBUG: Sleeping for (\d+).*', line)

    if match:
        return match.group(1)
    return None


def detect_gcp_start(file_monitor):
    """
    Detect module gcp-pubsub starts after restarting Wazuh.

    Parameters
    ----------
    file_monitor : FileMonitor
        File log monitor to detect events
    """
    file_monitor.start(timeout=60, callback=callback_detect_start_gcp)


def callback_received_messages_number(line):
    match = re.match(r'.*wm_gcp_run\(\): INFO: - INFO - Received and acknowledged (\d+) messages', line)
    if match:
        return match.group(1)
    return None


def callback_detect_all_gcp(line):
    match = re.match(r'.*wazuh-modulesd:gcp-pubsub\[\d+\].*', line)
    if match:
        return line
    return None


def callback_detect_gcp_alert(line):
    msg = r'.*Sending gcp event: (.+)$'
    match = re.match(msg, line)

    if match:
        return json.loads(str(match.group(1)))
    return None


def callback_detect_schedule_validate_parameters_warn(line):
    match = re.match(r'.*at _sched_scan_validate_parameters\(\): WARNING:.*', line)

    if match:
        return line
    return None


def callback_detect_schedule_validate_parameters_err(line):
    match = re.match(r'.*at _sched_scan_validate_parameters\(\): ERROR:.*', line)

    if match:
        return line
    return None


def callback_detect_gcp_read_err(line):
    match_err = re.match(r'.*wm_gcp_read\(\): ERROR:.*', line)
    match_warn = re.match(r'.*wm_gcp_read\(\): WARNING: File \'\S+\' not found.*', line)

    if match_err:
        return line
    elif match_warn:
        return line
    return None


def callback_detect_gcp_wmodule_err(line):
    match_err = re.match(r'.*read_main_elements\(\): ERROR: \(\d+\): Invalid element in the configuration.*', line)
    match_deb = re.match(r'.*Read_GCP\(\): DEBUG: Empty configuration for module \'gcp-pubsub\'', line)

    if match_err:
        return line
    elif match_deb:
        return line
    return None


def callback_detect_schedule_read_err(line):
    match = re.match(r'.*at sched_scan_read\(\): ERROR:.*', line)

    if match:
        return line
    return None


def publish(id_project, name_topic, credentials, repetitions=1, msg=None):
    if WAZUH_PATH in credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "{}".format(credentials)
    else:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "{}/{}".format(WAZUH_PATH, credentials)

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(id_project, name_topic)

    for number in range(repetitions):
        data = u"{}".format(msg)
        # Data must be a bytestring
        data = data.encode("utf-8")
        # Add two attributes, origin and username, to the message
        future = publisher.publish(topic_path, data, origin="python-sample", username="gcp")
