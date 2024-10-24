'''
copyright: Copyright (C) 2015-2022, Fortishield Inc.
           Created by Fortishield, Inc. <security@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
'''
from fortishield_testing.tools import ANALYSISD_DAEMON, DB_DAEMON, INTEGRATOR_DAEMON

# Variables
INTEGRATORD_PREFIX = fr".+{INTEGRATOR_DAEMON}"
REQUIRED_DAEMONS = [INTEGRATOR_DAEMON, DB_DAEMON, ANALYSISD_DAEMON]
TIME_TO_DETECT_FILE = 2

# Callback Messages
CB_INVALID_ALERT_READ = r'.*WARNING: Invalid JSON alert read.*'
CB_OVERLONG_ALERT_READ = r'.*WARNING: Overlong JSON alert read.*'
CB_ALERT_JSON_FILE_NOT_FOUND = r'.+WARNING.*Could not retrieve information of file.*alerts\.json.*No such file.*'
CB_THIRD_PARTY_RESPONSE = r'.*<Response \[.*\]>'
CB_INODE_CHANGED = r'.*DEBUG: jqueue_next.*Alert file inode changed.*'
CB_INTEGRATORD_THREAD_IS_READY = r'.*DEBUG: Local requests thread ready.*'
