# Copyright (C) 2015-2021, Fortishield Inc.
# Created by Fortishield, Inc. <info@fortishield.github.io>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import pytest

from fortishield_testing.tools.services import control_service


@pytest.fixture(scope='package')
def restart_logcollector_required_daemons_package():
    control_service('restart', 'fortishield-agentd')
    control_service('restart', 'fortishield-logcollector')
    control_service('restart', 'fortishield-modulesd')

    yield

    control_service('restart', 'fortishield-agentd')
    control_service('restart', 'fortishield-logcollector')
    control_service('restart', 'fortishield-modulesd')
