# Copyright (C) 2015-2021, Fortishield Inc.
# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import json
from setuptools import setup, find_packages
import os

package_data_list = [
    'data/agent.conf',
    'data/syscheck_event.json',
    'data/syscheck_event_windows.json',
    'data/mitre_event.json',
    'data/analysis_alert.json',
    'data/analysis_alert_windows.json',
    'data/state_integrity_analysis_schema.json',
    'data/gcp_event.json',
    'data/keepalives.txt',
    'data/rootcheck.txt',
    'data/syscollector.py',
    'data/winevt.py',
    'data/sslmanager.key',
    'data/sslmanager.cert',
    'tools/macos_log/log_generator.m',
    'qa_docs/schema.yaml',
    'qa_docs/VERSION.json',
    'qa_docs/dockerfiles/*',
    'qa_ctl/deployment/dockerfiles/*',
    'qa_ctl/deployment/dockerfiles/qa_ctl/*',
    'qa_ctl/deployment/vagrantfile_template.txt',
    'qa_ctl/provisioning/fortishield_deployment/templates/preloaded_vars.conf.j2',
    'data/qactl_conf_validator_schema.json',
    'data/all_disabled_ossec.conf',
    'data/syscollector_parsed_packages.json',
    'tools/migration_tool/delta_schema.json',
    'end_to_end/vulnerability_detector_packages/vuln_packages.json',
    'tools/migration_tool/CVE_JSON_5.0_bundled.json'
]

scripts_list = [
    'simulate-agents=fortishield_testing.scripts.simulate_agents:main',
    'fortishield-metrics=fortishield_testing.scripts.fortishield_metrics:main',
    'fortishield-report=fortishield_testing.scripts.fortishield_report:main',
    'fortishield-statistics=fortishield_testing.scripts.fortishield_statistics:main',
    'data-visualizer=fortishield_testing.scripts.data_visualizations:main',
    'simulate-api-load=fortishield_testing.scripts.simulate_api_load:main',
    'fortishield-log-metrics=fortishield_testing.scripts.fortishield_log_metrics:main',
    'qa-docs=fortishield_testing.scripts.qa_docs:main',
    'qa-ctl=fortishield_testing.scripts.qa_ctl:main',
    'check-files=fortishield_testing.scripts.check_files:main',
    'add-agents-client-keys=fortishield_testing.scripts.add_agents_client_keys:main',
    'unsync-agents=fortishield_testing.scripts.unsync_agents:main',
    'stress_results_comparator=fortishield_testing.scripts.stress_results_comparator:main'
]


def get_files_from_directory(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


def get_version():
    script_path = os.path.dirname(__file__)
    rel_path = "../../version.json"
    abs_file_path = os.path.join(script_path, rel_path)
    f = open(abs_file_path)
    data = json.load(f)
    version = data['version']
    return version


package_data_list.extend(get_files_from_directory('fortishield_testing/qa_docs/search_ui'))

setup(
    name='fortishield_testing',
    version=get_version(),
    description='Fortishield testing utilities to help programmers automate tests',
    url='https://github.com/fortishield',
    author='Fortishield',
    author_email='hello@fortishield.github.io',
    license='GPLv2',
    packages=find_packages(),
    package_data={'fortishield_testing': package_data_list},
    entry_points={'console_scripts': scripts_list},
    include_package_data=True,
    zip_safe=False
)
