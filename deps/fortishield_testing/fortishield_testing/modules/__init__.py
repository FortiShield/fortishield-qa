'''
copyright: Copyright (C) 2015-2023, Fortishield Inc.
           Created by Fortishield, Inc. <security@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
'''
import pytest

# Services Variables
FORTISHIELD_SERVICES_STOPPED = 'stopped'
FORTISHIELD_SERVICE_PREFIX = 'fortishield'
FORTISHIELD_SERVICES_STOP = 'stop'
FORTISHIELD_SERVICES_START = 'start'

# Configurations
DATA = 'data'
FORTISHIELD_LOG_MONITOR = 'fortishield_log_monitor'

# Marks Executions

TIER0 = pytest.mark.tier(level=0)
TIER1 = pytest.mark.tier(level=1)
TIER2 = pytest.mark.tier(level=2)

WINDOWS = pytest.mark.win32
LINUX = pytest.mark.linux
MACOS = pytest.mark.darwin
SOLARIS = pytest.mark.sunos5

AGENT = pytest.mark.agent
SERVER = pytest.mark.server

# Local internal options
WINDOWS_DEBUG = 'windows.debug'
SYSCHECK_DEBUG = 'syscheck.debug'
VERBOSE_DEBUG_OUTPUT = 2
