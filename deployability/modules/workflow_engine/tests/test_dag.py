# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2
import graphlib

from unittest.mock import patch, MagicMock, call
import pytest

from workflow_engine.workflow_processor import DAG


@pytest.fixture
def dag_mock(request) -> DAG:
    """Create a mocked dag instance."""
    reverse = request.param.get('reverse', False)
    def_tc = [
        {'task': 'task1', 'path': '/cmd1', 'args': [{"param1": "value1"}]},
        {'task': 'task2', 'path': '/cmd2', 'args': [{"param1": "value1"}]},
        {'task': 'task3', 'path': '/cmd3', 'args': [{"param1": "value1"}]},
    ]
    task_collection = request.param.get('task_collection', def_tc)
    gl_dag = graphlib.TopologicalSorter()

    dep_dict = {'task1': 'task2'}
    execution_plan_dict = request.param.get('execution_plan_dict', {})
    with patch.object(gl_dag, 'prepare'), \
        patch('workflow_engine.workflow_processor.DAG._DAG__build_dag',
              return_value=(gl_dag, dep_dict)), \
        patch('workflow_engine.workflow_processor.DAG._DAG__create_execution_plan',
              return_value=execution_plan_dict):
        dag = DAG(task_collection=task_collection, reverse=reverse)
    return dag


@pytest.mark.parametrize("reverse", [True, False])
@patch("workflow_engine.workflow_processor.DAG._DAG__build_dag")
@patch("workflow_engine.workflow_processor.DAG._DAG__create_execution_plan")
def test_dag_constructor(create_exec_plan_mock: MagicMock, build_dag_mock: MagicMock, reverse: bool):
    """Test ProcessTask constructor."""
    task_collection = [
        {'task': 'task1', 'path': '/cmd1', 'args': [{"param1": "value1"}]},
        {'task': 'task2', 'path': '/cmd2', 'args': [{"param1": "value1"}]},
        {'task': 'task3', 'path': '/cmd3', 'args': [{"param1": "value1"}]},
    ]
    gl_dag = graphlib.TopologicalSorter()

    dep_dict = {'task1': 'task2'}
    build_dag_mock.return_value = (gl_dag, dep_dict)
    plan_dict = {'task1', 'task2'}
    create_exec_plan_mock.return_value = plan_dict
    with patch.object(gl_dag, 'prepare') as prepare_mock:
        dag = DAG(task_collection=task_collection, reverse=reverse)

    assert dag.task_collection == task_collection
    assert dag.reverse == reverse
    assert dag.dag == gl_dag
    assert dag.dependency_tree == dep_dict
    assert isinstance(dag.to_be_canceled, set) and not dag.to_be_canceled
    assert dag.finished_tasks_status == {
        'failed': set(),
        'canceled': set(),
        'successful': set(),
    }
    assert dag.execution_plan == plan_dict
    build_dag_mock.assert_called_once()
    create_exec_plan_mock.assert_called_once_with(dep_dict)
    prepare_mock.assert_called_once()


@pytest.mark.parametrize('dag_mock',
                         [{'reverse': True}, {'reverse': False}],
                         indirect=True)
@pytest.mark.parametrize('is_active', [True, False])
def test_dag_is_active(is_active: bool, dag_mock: DAG):
    """Test DAG.is_active method."""
    with patch.object(dag_mock.dag, 'is_active', return_value=is_active) as is_active_mock:
        assert dag_mock.is_active() == is_active
    is_active_mock.assert_called_once()


@pytest.mark.parametrize('dag_mock',
                         [{'execution_plan_dict': {'task1', 'task2'} }], indirect=True)
def test_get_execution_plan(dag_mock: DAG):
    """Test DAG.get_execution_plan method."""
    assert dag_mock.get_execution_plan() == dag_mock.execution_plan


@pytest.mark.parametrize('dag_mock', [{}], indirect=True)
@pytest.mark.parametrize('task_name, status', [
    ('task1', 'failed'),
    ('task1', 'canceled'),
    ('task1', 'successful'),
    ('task1', 'non_existing_status'),
    ('non_existing_task', 'successful'),
    ('non_existing_task', 'non_existing_status'),
])
def test_set_status(task_name, status, dag_mock: DAG):
    """Test DAG.set_status method."""
    with patch.object(dag_mock.dag, "done") as done_mock:
        dag_mock.set_status(task_name=task_name, status=status)
    assert task_name in dag_mock.finished_tasks_status[status]
    done_mock.assert_called_once_with(task_name)


@pytest.mark.parametrize('dag_mock', [{}], indirect=True)
@pytest.mark.parametrize('in_cancel', [True, False])
def test_should_be_canceled(in_cancel, dag_mock: DAG):
    """Test DAG.should_be_canceled method."""
    if in_cancel:
        dag_mock.to_be_canceled.add('task1')
    else:
        if 'task1' in dag_mock.to_be_canceled:
            dag_mock.to_be_canceled.remove('task1')

    assert dag_mock.should_be_canceled(task_name='task1') == in_cancel


@pytest.mark.parametrize('dag_mock',
                         [{
                             'task_collection': [
                                {'task': 'task1', },
                                {'task': 'task2', 'depends-on': ['task1']},
                                {'task': 'task3', 'depends-on': ['task1']},
                                {'task': 'task4', 'depends-on': ['task1']},
                                {'task': 'task5', 'depends-on': ['task2', 'task3', 'task4']}
                                ]
                           },
                            {'task_collection': [
                                {'task': 'task1', },
                                {'task': 'task2', 'depends-on': ['task1']},
                                {'task': 'task3', 'depends-on': ['task1']},
                                {'task': 'task4', 'depends-on': ['task1']},
                                {'task': 'task5', 'depends-on': ['task2', 'task3', 'task4']}],
                                'reverse': True
                            }
                         ],
                         indirect=True)
def test_build_dag(dag_mock: DAG):
    """Test DAG.__build_dag method."""
    with patch('workflow_engine.workflow_processor.graphlib.TopologicalSorter.add') as mock_add:
        res_dag, res_dependency_dict = dag_mock._DAG__build_dag()
    assert isinstance(res_dag, graphlib.TopologicalSorter)
    call_list = []
    dependency_dict = {}
    for task in dag_mock.task_collection:
        dependencies = task.get('depends-on', [])
        task_name = task['task']
        if dag_mock.reverse:
            for dependency in dependencies:
                call_list.append(call(dependency, task_name))
        else:
            call_list.append(call(task_name, *dependencies))
        dependency_dict[task_name] = dependencies

    assert res_dependency_dict == dependency_dict
    mock_add.assert_has_calls(call_list, any_order=True)
