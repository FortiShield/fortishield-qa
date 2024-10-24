# Copyright (C) 2015-2021, Fortishield Inc.
# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import os
import subprocess
import sys
import time
import psutil

from fortishield_testing.tools import FORTISHIELD_PATH, get_service, FORTISHIELD_SOCKETS, QUEUE_DB_PATH, FORTISHIELD_OPTIONAL_SOCKETS
from fortishield_testing.tools.configuration import write_fortishield_conf
from fortishield_testing.modules import FORTISHIELD_SERVICES_START, FORTISHIELD_SERVICES_STOP


def restart_fortishield_daemon(daemon):
    """Restarts a Fortishield daemon.

    Use this function to avoid restarting the whole service and all of its daemons.

    Args:
        daemon (str): Name of the executable file of the daemon in /var/ossec/bin
    """
    for proc in psutil.process_iter(attrs=['name']):
        if proc.name() == daemon:
            proc.terminate()

    daemon_path = os.path.join(FORTISHIELD_PATH, 'bin')
    subprocess.check_call([f'{daemon_path}/{daemon}'])


def restart_fortishield_with_new_conf(new_conf, daemon='fortishield-syscheckd'):
    """Restart Fortishield service applying a new ossec.conf.

    Args:
        new_conf ( ET.ElementTree) : New config file.
        daemon (str, optional): Daemon to restart when applying the configuration.
    """
    write_fortishield_conf(new_conf)
    control_service('restart', daemon=daemon)


def delete_sockets(path=None):
    """Delete a list of Fortishield socket files or all of them if None is specified.

    Args:
        path (list, optional): Absolute socket path. Default `None`.
    """
    try:
        if path is None:
            path = os.path.join(FORTISHIELD_PATH, 'queue', 'sockets')
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
            if os.path.exists(os.path.join(FORTISHIELD_PATH, 'queue', 'db', 'wdb')):
                os.remove(os.path.join(FORTISHIELD_PATH, 'queue', 'db', 'wdb'))
            if os.path.exists(os.path.join(FORTISHIELD_PATH, 'queue', 'cluster', 'c-internal.sock')):
                os.remove(os.path.join(FORTISHIELD_PATH, 'queue', 'cluster', 'c-internal.sock'))
        else:
            for item in path:
                os.remove(item)
    except FileNotFoundError:
        pass


def control_service(action, daemon=None, debug_mode=False):
    """Perform the stop, start and restart operation with Fortishield.

    It takes care of the current OS to interact with the service and the type of installation (agent or manager).

    Args:
        action ({'stop', 'start', 'restart'}): Action to be done with the service/daemon.
        daemon (str, optional): Name of the daemon to be controlled. None for the whole Fortishield service. Default `None`.
        debug_mode (bool, optional) : Run the specified daemon in debug mode. Default `False`.
    Raises:
        ValueError: If `action` is not contained in {'start', 'stop', 'restart'}.
        ValueError: If the result is not equal to 0.
    """
    valid_actions = ('start', 'stop', 'restart')
    if action not in valid_actions:
        raise ValueError(f'action {action} is not one of {valid_actions}')

    if sys.platform == 'win32':
        if action == 'restart':
            control_service('stop')
            control_service('start')
            result = 0
        else:
            error_109_windows_retry = 3
            for _ in range(error_109_windows_retry):
                command = subprocess.run(["net", action, "FortishieldSvc"], stderr=subprocess.PIPE)
                result = command.returncode
                if result == 0:
                    break
                else:
                    error = command.stderr.decode()
                    if 'The service is starting or stopping' in error:
                        time.sleep(1)
                        continue
                    if action == 'stop' and 'The Fortishield service is not started.' in error:
                        result = 0
                        break
                    if action == 'start' and 'The requested service has already been started.' in error:
                        result = 0
                        break
                    elif "System error 109 has occurred" not in error:
                        print(f"Unexpected error when control_service failed with the following error: {error}")
                        break
    else:  # Default Unix
        if daemon is None:
            if sys.platform == 'darwin' or sys.platform == 'sunos5':
                result = subprocess.run([f'{FORTISHIELD_PATH}/bin/fortishield-control', action]).returncode
            else:
                result = subprocess.run(['service', get_service(), action]).returncode
            action == 'stop' and delete_sockets()
        else:
            if action == 'restart':
                control_service('stop', daemon=daemon)
                control_service('start', daemon=daemon)
            elif action == 'stop':
                processes = []

                for proc in psutil.process_iter():
                    try:
                        if daemon in ['fortishield-clusterd', 'fortishield-apid']:
                            for file in os.listdir(f'{FORTISHIELD_PATH}/var/run'):
                                if daemon in file:
                                    pid = file.split("-")
                                    pid = pid[2][0:-4]
                                    if pid == str(proc.pid):
                                        processes.append(proc)
                        elif daemon in proc.name() or daemon in ' '.join(proc.cmdline()):
                            processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                try:
                    for proc in processes:
                        proc.terminate()

                    _, alive = psutil.wait_procs(processes, timeout=5)

                    for proc in alive:
                        proc.kill()
                except psutil.NoSuchProcess:
                    pass

                delete_sockets(FORTISHIELD_SOCKETS[daemon])
            else:
                daemon_path = os.path.join(FORTISHIELD_PATH, 'bin')
                start_process = [f'{daemon_path}/{daemon}'] if not debug_mode else [f'{daemon_path}/{daemon}', '-dd']
                subprocess.check_call(start_process)
            result = 0

    if result != 0:
        raise ValueError(f"Error when executing {action} in daemon {daemon}. Exit status: {result}")


def restart_fortishield_function():
    """Restarts Fortishield."""
    control_service(FORTISHIELD_SERVICES_STOP)
    control_service(FORTISHIELD_SERVICES_START)


def get_process(search_name):
    """Search process by its name.

    Args:
        search_name (str): Name of the process to be fetched.

    Returns:
        `psutil.Process` or None: First occurrence of the process object matching the `search_name` or
            None if no process has been found.
    """
    for proc in psutil.process_iter(attrs=['name']):
        if proc.name() == search_name:
            return proc

    return None


def search_process(search_pattern):
    """Search process by its name.

    Args:
        search_pattern (str): Pattern of the process to be fetched.

    Returns:
        List: List of dictionaries with name and pid values of founded processes.
    """
    processes = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'username']):
        if search_pattern == proc.name():
            pinfo = proc.as_dict(attrs=['pid', 'name'])
            processes += [pinfo]
    return processes


def get_process_cmd(search_cmd):
    """Search process by its command line.

    Args:
        search_cmd (str): Name of the command to be fetched.

    Returns:
        `psutil.Process` or None: First occurrence of the process object matching the `search_cmd` or
            None if no process has been found.
    """
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        command = next((command for command in proc.cmdline() if search_cmd in command), None)
        if command:
            return proc


def check_daemon_status(target_daemon=None, running_condition=True, timeout=10, extra_sockets=[]):
    """Wait until Fortishield daemon's status matches the expected one. If timeout is reached and the status didn't match,
       it raises a TimeoutError.

    Args:
        target_daemon (str, optional):  Fortishield daemon to check. Default `None`. None means all.
        running_condition (bool, optional): True if the daemon is expected to be running False
            if it is expected to be stopped. Default `True`.
        timeout (int, optional): Timeout value for the check. Default `10` seconds.
        extra_sockets (list, optional): Additional sockets to check. They may not be present in default configuration.

    Raises:
        TimeoutError: If the daemon status is wrong after timeout seconds.
    """
    condition_met = False
    start_time = time.time()
    elapsed_time = 0

    while elapsed_time < timeout and not condition_met:
        if sys.platform == 'win32':
            condition_met = check_if_process_is_running('fortishield-agent.exe') == running_condition
        else:
            control_status_output = subprocess.run([f'{FORTISHIELD_PATH}/bin/fortishield-control', 'status'],
                                                   stdout=subprocess.PIPE).stdout.decode()
            condition_met = True
            for lines in control_status_output.splitlines():
                daemon_status_tokens = lines.split()
                current_daemon = daemon_status_tokens[0]
                daemon_status = ' '.join(daemon_status_tokens[1:])
                daemon_running = daemon_status == 'is running...'
                if current_daemon == target_daemon or target_daemon is None:
                    if current_daemon in FORTISHIELD_SOCKETS.keys():
                        socket_set = {path for path in FORTISHIELD_SOCKETS[current_daemon]}
                    else:
                        socket_set = set()
                    # We remove optional sockets and add extra sockets to the set to check
                    socket_set.difference_update(FORTISHIELD_OPTIONAL_SOCKETS)
                    socket_set.update(extra_sockets)
                    # Check specified socket/s status
                    for socket in socket_set:
                        if os.path.exists(socket) != running_condition:
                            condition_met = False
                    if daemon_running != running_condition:
                        condition_met = False
        if not condition_met:
            time.sleep(1)
        elapsed_time = time.time() - start_time

    if not condition_met:
        raise TimeoutError(f"{target_daemon} does not meet condition: running = {running_condition}")
    return condition_met


def delete_dbs():
    """Delete all fortishield-db databases."""
    for root, dirs, files in os.walk(QUEUE_DB_PATH):
        for file in files:
            os.remove(os.path.join(root, file))


def check_if_process_is_running(process_name):
    """Check if process is running.

    Args:
        process_name (str): Name of process.

    Returns
        boolean: True if process is running, False otherwise.
    """
    is_running = False
    try:
        is_running = process_name in (p.name() for p in psutil.process_iter())
    except psutil.NoSuchProcess:
        pass

    return is_running


def control_event_log_service(control):
    """Control Windows event log service.

    Args:
        control (str): Start or Stop.

    Raises:
        ValueError: If the event log channel does not start/stop correctly.
    """
    for _ in range(10):
        control_sc = 'disabled' if control == 'stop' else 'auto'

        try:
            subprocess.run(f'sc.exe config netprofm start= {control_sc}', stderr=subprocess.PIPE)
        except Exception:
            pass

        command = subprocess.run(f'sc.exe config eventlog start= {control_sc}', stderr=subprocess.PIPE)

        result = command.returncode
        if result != 0:
            raise ValueError(f'Event log service did not stop correctly')

        command = subprocess.run(f"net {control} eventlog /y", stderr=subprocess.PIPE)

        try:
            subprocess.run(f"net {control} netprofm /y", stderr=subprocess.PIPE)
        except Exception:
            pass

        result = command.returncode

        if ("The requested service has already been started." in str(command.stderr)) or  \
           ("The Windows Event Log service is not started." in str(command.stderr)) or result == 0:
            break
        time.sleep(1)
    else:
        raise ValueError(f"Event log service did not stop correctly")
    time.sleep(1)
