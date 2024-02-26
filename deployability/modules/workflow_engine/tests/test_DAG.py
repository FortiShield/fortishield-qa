# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2

import pytest
from workflow_engine.task import ProcessTask

@pytest.fixture
def task(request) -> ProcessTask:
    """Shared fixture to create task."""
    task_name, task_parms = request.param
    return ProcessTask(task_name=task_name, task_parameters=task_parms)


@pytest.mark.parametrize("task", [('task1', {"param1": "value1"})], indirect=True)
def test_process_task_constructor(task):
    """Test ProcessTask constructor."""
    assert task.task_name == 'task1'
    assert task.task_parameters == {"param1": "value1"}


def test_process_task_execute(task):
    """Test ProcessTask.execute method."""
    assert True


def test_process_dag_constructor(task):
    """Test DAG constructor."""
    assert True
