# Copyright (C) 2015-2023, Fortishield Inc.
# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

from fortishield_testing import MODULESD_DEBUG, VERBOSE_DEBUG_OUTPUT

# Variables
TEMP_FILE_PATH = '/tmp'

# Setting Local_internal_option file
SCA_DEFAULT_LOCAL_INTERNAL_OPTIONS = {MODULESD_DEBUG: str(VERBOSE_DEBUG_OUTPUT)}