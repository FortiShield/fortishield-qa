# Copyright (C) 2015-2021, Fortishield Inc.
# Created by Fortishield, Inc. <info@fortishield.github.io>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import pytest

from fortishield_testing.github import detect_github_start


@pytest.fixture(scope='module')
def wait_for_github_start(get_configuration, request):
    # Wait for module github starts
    file_monitor = getattr(request.module, 'fortishield_log_monitor')
    detect_github_start(file_monitor)
