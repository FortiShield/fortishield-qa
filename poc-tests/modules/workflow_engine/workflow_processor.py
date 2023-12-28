# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2

import graphlib
import concurrent.futures
import time
import logging
from itertools import product
import yaml
from .task import Task, ProcessTask, DummyTask, DummyRandomTask


class WorkflowProcessor:
    """Class for processing a workflow."""

    def __init__(self, workflow_file_path: str, dry_run: bool, threads: int):
        """
        Initialize WorkflowProcessor.

        Args:
            workflow_file_path (str): Path to the workflow file (YAML format).
            dry_run (bool): Display the plan without executing tasks.
            threads (int): Number of threads to use for parallel execution.
        """
        self.workflow_data = self.load_workflow(workflow_file_path)
        self.tasks = self.workflow_data.get('tasks', [])
        self.variables = self.workflow_data.get('variables', {})
        self.task_collection = self.process_workflow()
        self.static_workflow_validation()
        self.failed_tasks = set()
        self.logger = self.setup_logger()
        self.dry_run = dry_run
        self.threads = threads

    def setup_logger(self, log_format: str = 'plain', log_level: str = 'INFO') -> logging.Logger:
        """
        Set up the logger.

        Args:
            log_format (str): Log format (plain or json).
            log_level (str): Log level.

        Returns:
            logging.Logger: Logger instance.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)

        # Clear existing handlers to avoid duplicates
        for handler in logger.handlers:
            logger.removeHandler(handler)

        if log_format == 'json':
            formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "tag": "%(tag)s"}', datefmt="%Y-%m-%d %H:%M:%S")
        else:
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        # Add a console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def load_workflow(self, file_path: str) -> dict:
        """
        Load the workflow data from a file.

        Args:
            file_path (str): Path to the workflow file.

        Returns:
            dict: Workflow data.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def replace_placeholders(self, element: str, values: dict, parent_key: str = None):
        """
        Recursively replace placeholders in a dictionary or list.

        Args:
            element (Any): The element to process.
            values (dict): The values to replace placeholders.
            parent_key (str): The parent key for nested replacements.

        Returns:
            Any: The processed element.
        """
        if isinstance(element, dict):
            return {key: self.replace_placeholders(value, values, key) for key, value in element.items()}
        elif isinstance(element, list):
            return [self.replace_placeholders(sub_element, values, parent_key) for sub_element in element]
        elif isinstance(element, str):
            return element.format_map(values)
        else:
            return element

    def expand_task(self, task: dict, variables: dict):
        """
        Expand a task with variable values.

        Args:
            task (dict): The task to expand.
            variables (dict): Variable values.

        Returns:
            List[dict]: List of expanded tasks.
        """
        expanded_tasks = []

        if 'foreach' in task:
            loop_variables = task.get('foreach', [{}])

            variable_names = [loop_variable_data.get('variable') for loop_variable_data in loop_variables]
            as_identifiers = [loop_variable_data.get('as') for loop_variable_data in loop_variables]

            variable_values = [variables.get(name, []) for name in variable_names]

            for combination in product(*variable_values):
                variables_with_items = {**variables, **dict(zip(as_identifiers, combination))}
                expanded_tasks.append(self.replace_placeholders(task, variables_with_items))
        else:
            expanded_tasks.append(self.replace_placeholders(task, variables))

        return expanded_tasks

    def process_workflow(self):
        """Process the workflow and return a list of tasks."""
        task_collection = []
        for task in self.tasks:
            task_collection.extend(self.expand_task(task, self.variables))
        return task_collection

    def static_workflow_validation(self):
        """Validate the workflow against static criteria."""
        def check_duplicated_tasks(self):
            """Validate task name duplication."""
            task_name_counts = {task['task']: 0 for task in self.task_collection}
            
            for task in self.task_collection:
                task_name_counts[task['task']] += 1

            duplicates = [name for name, count in task_name_counts.items() if count > 1]

            if duplicates:
                raise ValueError(f"Duplicated task names: {', '.join(duplicates)}")

        def check_not_existing_tasks(self):
            """Validate task existance."""
            task_names = {task['task'] for task in self.task_collection}
            
            for dependencies in [task.get('depends-on', []) for task in self.task_collection]:
                non_existing_dependencies = [dependency for dependency in dependencies if dependency not in task_names]
                if non_existing_dependencies:
                    raise ValueError(f"Tasks do not exist: {', '.join(non_existing_dependencies)}")
        
        validations = [check_duplicated_tasks, check_not_existing_tasks]
        for validation in validations:
            validation(self)

    def build_dependency_graph(self, reverse=False):
        """Build a dependency graph for the tasks."""
        dependency_dict = {}
        dag = graphlib.TopologicalSorter()

        for task in self.task_collection:
            task_name = task['task']
            dependencies = task.get('depends-on', [])

            if reverse:
                for dependency in dependencies:
                    dag.add(dependency, task_name)
            else:
                dag.add(task_name, *dependencies)

            dependency_dict[task_name] = dependencies

        return dag, dependency_dict

    def execute_task(self, task: dict, action) -> None:
        """Execute a task."""
        task_name = task['task']

        self.logger.info("Starting task", extra={'tag': task_name})
        start_time = time.time()

        try:
            task_object = self.create_task_object(task, action)
            task_object.execute()
            # Pass the tag to the tag_formatter function if it exists
            tag_info = self.logger.tag_formatter(task_name) if hasattr(self.logger, 'tag_formatter') else {}
            self.logger.info("Finished task in %.2f seconds", time.time() - start_time, extra={'tag': task_name, **tag_info})
        except Exception as e:
            # Pass the tag to the tag_formatter function if it exists
            tag_info = self.logger.tag_formatter(task_name) if hasattr(self.logger, 'tag_formatter') else {}
            self.logger.error("Task failed with error: %s", e, extra={'tag': task_name, **tag_info})
            self.failed_tasks.add(task_name)
            # Handle the exception or re-raise if necessary
            raise

    def create_task_object(self, task: dict, action) -> Task:
        """Create and return a Task object based on task type."""
        task_type = task[action]['this']

        task_classes = {
            'process': ProcessTask,
            'dummy': DummyTask,
            'dummy-random': DummyRandomTask,
        }

        task_class = task_classes.get(task_type)

        if task_class is not None:
            return task_class(task['task'], task[action]['with'], self.logger)

        raise ValueError(f"Unknown task type '{task_type}'.")

    def get_root_tasks(self, dependency_dict: dict) -> set:
        """Get root tasks from the dependency dictionary."""
        all_tasks = set(dependency_dict.keys())
        dependent_tasks = set(dep for dependents in dependency_dict.values() for dep in dependents)
        return all_tasks - dependent_tasks

    def print_execution_plan(self, task_name: str, dependency_dict: dict, level: int = 0) -> None:
        """Print the execution plan recursively."""
        if task_name not in dependency_dict:
            return

        dependencies = dependency_dict[task_name]
        indentation = "    " * level
        self.logger.info("%s%s", indentation, task_name)

        for dependency in dependencies:
            self.print_execution_plan(dependency, dependency_dict, level + 1)

    def execute_tasks_parallel(self) -> None:
        """Execute tasks in parallel."""
        dag, dependency_dict = self.build_dependency_graph()

        if self.dry_run:
            # Display the execution plan without executing tasks
            root_tasks = self.get_root_tasks(dependency_dict)
            for root_task in root_tasks:
                self.print_execution_plan(root_task, dependency_dict)
        else:
            dag.prepare()

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {}

                while True:
                    if not dag.is_active() or self.failed_tasks:
                        break

                    for task_name in dag.get_ready():
                        dependencies = dependency_dict[task_name]

                        if any(dep in self.failed_tasks for dep in dependencies):
                            self.logger.info("[%s] Skipping task due to dependency failure", task_name)
                            self.failed_tasks.add(task_name)
                            dag.done(task_name)
                            continue

                        dependent_futures = [futures[d] for d in dependencies if d in futures]

                        concurrent.futures.wait(dependent_futures)

                        task = next(t for t in self.task_collection if t['task'] == task_name)
                        future = executor.submit(self.execute_task, task, 'do')
                        futures[task_name] = future

                        dag.done(task_name)

            # Wait for all tasks to complete
            concurrent.futures.wait(futures.values())

            # Now execute tasks based on the reverse DAG
            reverse_dag, reverse_dependency_dict = self.build_dependency_graph(reverse=True)

            reverse_dag.prepare()

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
                reverse_futures = {}

                while True:
                    if not reverse_dag.is_active() or self.failed_tasks:
                        break

                    for task_name in reverse_dag.get_ready():
                        dependencies = reverse_dependency_dict[task_name]
                        
                        if any(dep in self.failed_tasks for dep in dependencies):
                            self.logger.info("[%s] Skipping task due to dependency failure", task_name)
                            self.failed_tasks.add(task_name)
                            reverse_dag.done(task_name)
                            continue

                        dependent_futures = [reverse_futures[d] for d in dependencies if d in reverse_futures]

                        concurrent.futures.wait(dependent_futures)

                        task = next(t for t in self.task_collection if t['task'] == task_name)
                        if 'cleanup' in task:
                            future = executor.submit(self.execute_task, task, 'cleanup')
                            reverse_futures[task_name] = future
                        reverse_dag.done(task_name)

            # Wait for all tasks to complete
            concurrent.futures.wait(reverse_futures.values())

    def main(self) -> None:
        """Main entry point."""
        self.execute_tasks_parallel()

    def abort_execution(self, executor: concurrent.futures.ThreadPoolExecutor, futures: dict) -> None:
        """Abort the execution of tasks."""
        for future in concurrent.futures.as_completed(futures.values()):
            try:
                _ = future.result()
            except Exception as e:
                self.logger.error("Error in aborted task: %s", e)

        executor.shutdown(wait=False)
