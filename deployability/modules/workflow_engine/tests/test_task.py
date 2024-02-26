# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2
from subprocess import CompletedProcess, CalledProcessError
from unittest.mock import patch
import pytest

from workflow_engine.task import ProcessTask

@pytest.fixture
def task(request) -> ProcessTask:
    """Shared fixture to create task."""
    task_name, task_parms = request.param
    return ProcessTask(task_name=task_name, task_parameters=task_parms)


@pytest.mark.parametrize("task", [('task1', {"param1": "value1"})], indirect=True)
def test_process_task_constructor(task: ProcessTask):
    """Test ProcessTask constructor."""
    assert task.task_name == 'task1'
    assert task.task_parameters == {"param1": "value1"}

@pytest.mark.parametrize("task", [('task1', {"path": "/mypath", "args": {"param1": "value1"}}),
                                  ('task2', {"path": "/mypath", "args": "arg1"})], indirect=True)
@pytest.mark.parametrize("subproc_retval", [1, 0])
@pytest.mark.parametrize("subproc_run_exc", [1, 0])
@patch("workflow_engine.logger.logger")
def test_process_task_execute(logger_mock, subproc_retval: int, subproc_run_exc: Exception,
                              task: ProcessTask):
    """Test ProcessTask.execute method."""
    results = {}
    results["task1"] = {"parm_list": [task.task_parameters['path'], ["--param1=value1"]]}
    results["task2"] = {"parm_list": [task.task_parameters['path'], ["arg1"]]}
    ret = CompletedProcess(args="", returncode=subproc_retval)
    with patch("workflow_engine.task.subprocess.run", return_value=ret):
        if subproc_retval:
            with pytest.raises(CalledProcessError):
                task.execute()
        else:
            task.execute()
    assert True
