# Copyright (C) 2015-2022, Fortishield Inc.

# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import pytest

from fortishield_testing.fim import LOG_FILE_PATH, detect_initial_scan, detect_realtime_start, detect_whodata_start
from fortishield_testing.tools.file import truncate_file
from fortishield_testing.tools.monitoring import FileMonitor
from fortishield_testing.tools.services import control_service


@pytest.fixture(scope='module')
def restart_syscheckd(get_configuration, request):
    """
    Reset ossec.log and start a new monitor.
    """
    control_service('stop', daemon='fortishield-syscheckd')
    truncate_file(LOG_FILE_PATH)
    file_monitor = FileMonitor(LOG_FILE_PATH)
    setattr(request.module, 'fortishield_log_monitor', file_monitor)
    control_service('start', daemon='fortishield-syscheckd')


@pytest.fixture(scope='module')
def wait_for_fim_start(get_configuration, request):
    """
    Wait for realtime start, whodata start or end of initial FIM scan.
    """
    file_monitor = getattr(request.module, 'fortishield_log_monitor')
    mode_key = 'fim_mode' if 'fim_mode2' not in get_configuration['metadata'] else 'fim_mode2'

    try:
        if get_configuration['metadata'][mode_key] == 'realtime':
            detect_realtime_start(file_monitor)
        elif get_configuration['metadata'][mode_key] == 'whodata':
            detect_whodata_start(file_monitor)
        else:  # scheduled
            detect_initial_scan(file_monitor)
    except KeyError:
        detect_initial_scan(file_monitor)


@pytest.fixture(scope='module')
def wait_for_fim_start_sync(request):
    """
    Wait for the sync initial FIM scan.
    """
    file_monitor = getattr(request.module, 'fortishield_log_monitor')
    detect_initial_scan(file_monitor)
