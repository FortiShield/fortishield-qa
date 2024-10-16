import os
from tempfile import gettempdir

from fortishield_testing.qa_ctl.provisioning.ansible.ansible_playbook import AnsiblePlaybook
from fortishield_testing.qa_ctl.provisioning.ansible.ansible_task import AnsibleTask
from fortishield_testing.tools.time import get_current_timestamp

OS_SYSTEM = ['centos', 'ubuntu']
OS_PLATFORM = ['linux', 'windows']
PACKAGE_MANAGER = {'centos': 'RPM', 'ubuntu': 'DEB'}
PLAYBOOSK_PATH = os.path.join(gettempdir(), 'fortishield_playbooks')


def validate_playbook_parameters(parameters):
    """Validate if the required parameters to build the playbook are specified.

    Raises:
        ValueError: If a required playbook parameter has not been specified.
    """
    required_parameters = ['tasks_list']

    for required_parameter in required_parameters:
        if required_parameter not in parameters.keys():
            raise ValueError(f"{required_parameter} is a required parameter to generate the playbook.")


def install_fortishield(fortishield_target, package_name, package_url, package_destination, os_system, os_platform,
                  playbook_parameters=None):
    """Generate the playbook to install Fortishield.

    Args:
        fortishield_target (str): Fortishield target [manager or agent].
        package_name (str): Name of the package to be installed.
        package_url (str): URL of the package to be installed.
        package_destination (str): Destination folder where the package will be downloaded.
        os_system (str): Operating system where the test will be launched.
        os_platform (str): Platform where the package will be installed.
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Raises:
        ValueError: If os_system or os_platform has not an expected value.

    Returns:
        str: Playbook file path generated.
    """
    tasks = []
    _os_system = _clean_os_system(os_system)

    if os_platform == 'linux':
        if PACKAGE_MANAGER[_os_system] == 'RPM':
            tasks = _install_fortishield_rpm(package_name, package_url, package_destination, fortishield_target)
        elif PACKAGE_MANAGER[_os_system] == 'DEB':
            tasks = _install_fortishield_deb(package_name, package_url, package_destination, fortishield_target)
        else:
            raise ValueError(f"{os_system} is not supported in PlaybookGenerator")
    else:
        raise ValueError(f"{os_platform} is not supported in PlaybookGenerator")

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'install_fortishield', 'tasks_list': tasks})

    return _build_playbook(parameters)


def upgrade_fortishield(package_name, package_url, package_destination, os_system, os_platform, playbook_parameters=None):
    """Generate the playbook to upgrade Fortishield.

    Args:
        package_name (str): Name of the package to be installed.
        package_url (str): URL of the package to be installed.
        package_destination (str): Destination folder where the package will be downloaded.
        os_system (str): Operating system where the test will be launched.
        os_platform (str): Platform where the package will be installed.
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Raises:
       ValueError: If os_system or os_platform has not an expected value.

    Returns:
        str: Playbook file path generated.
    """
    tasks = []
    _os_system = _clean_os_system(os_system)

    if os_platform == 'linux':
        if PACKAGE_MANAGER[_os_system] == 'RPM':
            tasks = _upgrade_fortishield_rpm(package_name, package_url, package_destination)
        elif PACKAGE_MANAGER[_os_system] == 'DEB':
            tasks = _upgrade_fortishield_deb(package_name, package_url, package_destination)
        else:
            raise ValueError(f"{os_system} is not supported in PlaybookGenerator")
    else:
        raise ValueError(f"{os_platform} is not supported in PlaybookGenerator")

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'upgrade_fortishield', 'tasks_list': tasks})

    return _build_playbook(parameters)


def uninstall_fortishield(fortishield_target, os_system, os_platform, playbook_parameters=None):
    """Generate the playbook to uninstall Fortishield.

    Args:
        fortishield_target (str): Fortishield target [manager or agent].
        os_system (str): Operating system where the test will be launched.
        os_platform (str): Platform where the package will be installed.
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Raises:
        ValueError: If os_system or os_platform has not an expected value.

    Returns:
        str: Playbook file path generated.
    """
    tasks = []
    _os_system = _clean_os_system(os_system)

    if os_platform == 'linux':
        if PACKAGE_MANAGER[_os_system] == 'RPM':
            tasks = _uninstall_fortishield_rpm(fortishield_target)
        elif PACKAGE_MANAGER[_os_system] == 'DEB':
            tasks = _uninstall_fortishield_deb(fortishield_target)
        else:
            raise ValueError(f"{os_system} is not supported in PlaybookGenerator")
    else:
        raise ValueError(f"{os_platform} is not supported in PlaybookGenerator")

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'uninstall_fortishield', 'tasks_list': tasks})

    return _build_playbook(parameters)


def run_linux_commands(commands, playbook_parameters=None):
    """Generate a playbook to run linux commands.

    Args:
        commands (list(str)): Commands to run with the playbook. [command1, command2, ...]
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Returns:
        str: Playbook file path generated.
    """
    tasks = _run_linux_commands(commands)

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'run_linux_commands', 'tasks_list': tasks})

    return _build_playbook(parameters)


def download_files(files_data, playbook_parameters=None):
    """Generate a playbook to download files.

    Args:
        files_data (list(dict)): URL and download destination info. [{url: destination}, ...]
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Returns:
        str: Playbook file path generated.
    """
    tasks = _download_files(files_data)

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'download_files', 'tasks_list': tasks})

    return _build_playbook(parameters)


def fetch_files(files_data, playbook_parameters=None):
    """Generate a playbook to fetch files.

    Args:
        files_data (list(dict)): Source and destination data. [{remote_src: local_destination}, ...]
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Returns:
        str: Playbook file path generated.
    """
    tasks = _fetch_files(files_data)

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'fetch_files', 'tasks_list': tasks})

    return _build_playbook(parameters)


def delete_files(files_path, playbook_parameters=None):
    """Generate a playbook to delete files.

    Args:
        files_path (list(str)): List of files path to delete. [file_path1, file_path2, ...]
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Returns:
        str: Playbook file path generated.
    """
    tasks = _delete_files(files_path)

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'delete_files', 'tasks_list': tasks})

    return _build_playbook(parameters)


def wait_seconds(num_seconds, playbook_parameters=None):
    """Generate a playbook to wait for the indicated time.

    Args:
        num_seconds (int): Number of seconds to wait.
        playbook_parameters (dict): Extra non-tasks playbook parameters.

    Returns:
        str: Playbook file path generated.
    """
    tasks = _wait_seconds(num_seconds)

    parameters = dict(**playbook_parameters) if playbook_parameters else {}
    parameters.update({'name': 'wait_seconds', 'tasks_list': tasks})

    return _build_playbook(parameters)


# -------------------------------------------------------------------------------------------------------------------- #
#                                        BUILDER AND UTILS FUNCTION                                                    #
# -------------------------------------------------------------------------------------------------------------------- #


def _build_playbook(parameters):
    """Generate the playbook with the specific parameters.

    Args:
        parameters (dict): Parameters of the playbook to be generated.

    Returns:
        str: Playbook file path generated.
    """
    # Validate if the required parameters to build the playbook are specified.
    validate_playbook_parameters(parameters)

    current_timestamp = str(get_current_timestamp()).replace('.', '_')
    playbook_file_path = os.path.join(PLAYBOOSK_PATH,
                                      f"{parameters['name']}_{current_timestamp}.yaml")

    playbook_parameters = dict(**parameters) if parameters else {}
    playbook_parameters.update({'playbook_file_path': playbook_file_path, 'generate_file': True})

    playbook = AnsiblePlaybook(**playbook_parameters)

    return playbook.playbook_file_path


def _clean_os_system(os_system):
    """Clean the operating system version, returning only the system.

    Args:
        os_system (str): Operating system.

    Raises:
        ValueError: If the os_system has an invalid value.

    Returns:
        str: Operating system without the version.
    """
    if 'centos' in os_system:
        return 'centos'
    elif 'ubuntu' in os_system:
        return 'ubuntu'
    else:
        raise ValueError(f"{os_system} is not allowed in PlaybookGenerator module")


# -------------------------------------------------------------------------------------------------------------------- #
#                                        PLAYBOOK TASKS DEFINITION                                                     #
# -------------------------------------------------------------------------------------------------------------------- #


def _download_fortishield_package(package_url, package_destination):
    """Ansible tasks to download a package.

    Args:
        package_url (str): URL of the package to be downloaded.
        package_destination (str): Destination where the package will be stored

    Returns:
        list(AnsibleTask): Ansible tasks to download the fortishield package.
    """
    return [
        AnsibleTask({
            'name': 'Download Fortishield package',
            'get_url': {
                'url': package_url,
                'dest': package_destination,
                'mode': '0755'
            },
            'register': 'download_package',
            'retries': 6,
            'delay': 10,
            'until': 'download_package is success'
        })
    ]


def _start_fortishield_manager_systemd_service():
    """"Ansible tasks to start the fortishield-manager service with systemd.

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': 'Start Fortishield Manager service with systemd',
            'become': True,
            'ansible.builtin.systemd': {
              'state': 'started',
              'name': 'fortishield-manager'
            }
        })
    ]


def _start_fortishield_agent_systemd_service():
    """Ansible tasks to start the fortishield-agent service with systemd.

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': 'Start Fortishield Agent service with systemd',
            'become': True,
            'ansible.builtin.systemd': {
              'state': 'started',
              'name': 'fortishield-agent'
            }
        })
    ]


def _stop_fortishield_manager_systemd_service():
    """Ansible tasks to stop the fortishield-manager service with systemd.

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': 'Start Fortishield Manager service with systemd',
            'become': True,
            'ansible.builtin.systemd': {
              'state': 'stopped',
              'name': 'fortishield-manager'
            }
        })
    ]


def _stop_fortishield_agent_systemd_service():
    """Ansible tasks to stop the fortishield-agent service with systemd.

    Returns:
       list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': 'Start Fortishield Agent service with systemd',
            'become': True,
            'ansible.builtin.systemd': {
              'state': 'stopped',
              'name': 'fortishield-agent'
            }
        })
    ]


def _start_fortishield_control_service(fortishield_target):
    """Ansible tasks to start the fortishield-agent or fortishield-manager using fortishield-control.

    Args:
        fortishield_target (str): Fortishield target [manager or agent].

    Returns:
       list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': f"Start Fortishield {fortishield_target} service with systemd",
            'become': True,
            'shell': '/var/ossec/bin/fortishield-control start',
        })
    ]


def _stop_fortishield_control_service(fortishield_target):
    """Ansible tasks to stop the fortishield-agent or fortishield-manager using fortishield-control.

    Args:
        fortishield_target (str): Fortishield target [manager or agent].

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': f"Stop Fortishield {fortishield_target} service with systemd",
            'become': True,
            'shell': '/var/ossec/bin/fortishield-control stop',
        })
    ]


def _install_fortishield_rpm(package_name, package_url, package_destination, fortishield_target):
    """Ansible tasks to install a fortishield RPM package.

    Args:
        package_name (str): Name of the package to be installed.
        package_url (str): URL of the package to be installed.
        package_destination (str): Destination folder where the package will be downloaded.
        fortishield_target (str): Fortishield target [manager or agent].

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    tasks = []

    tasks.extend(_download_fortishield_package(package_url, package_destination))
    tasks.append(
        AnsibleTask({
            'name': 'Install Fortishield RPM package',
            'become': True,
            'shell': f"yum install -y {package_name}",
            'args': {
                'chdir': package_destination
            },
            'register': 'rpm_install',
            'retries': 6,
            'delay': 10,
            'until': 'rpm_install is success',
        })
    )
    if 'manager' in fortishield_target:
        tasks.extend(_start_fortishield_manager_systemd_service())
    elif 'agent' in fortishield_target:
        tasks.extend(_start_fortishield_agent_systemd_service())

    return tasks


def _install_fortishield_deb(package_name, package_url, package_destination, fortishield_target):
    """Ansible tasks to install a fortishield DEB package.

    Args:
        package_name (str): Name of the package to be installed.
        package_url (str): URL of the package to be installed.
        package_destination (str): Destination folder where the package will be downloaded.
        fortishield_target (str): Fortishield target [manager or agent].

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    tasks = []

    tasks.extend(_download_fortishield_package(package_url, package_destination))
    tasks.append(
        AnsibleTask({
            'name': 'Install Fortishield DEB package',
            'become': True,
            'apt': {'deb': f"{package_destination}/{package_name}"},
            'register': 'deb_install',
            'retries': 6,
            'delay': 10,
            'until': 'deb_install is success',
        })
    )
    if 'manager' in fortishield_target:
        tasks.extend(_start_fortishield_manager_systemd_service())
    elif 'agent' in fortishield_target:
        tasks.extend(_start_fortishield_agent_systemd_service())

    return tasks


def _upgrade_fortishield_rpm(package_name, package_url, package_destination):
    """Ansible tasks to upgrade a fortishield RPM package.

    Args:
        package_name (str): Name of the package to be installed.
        package_url (str): URL of the package to be installed.
        package_destination (str): Destination folder where the package will be downloaded.

    Returns:
       list(AnsibleTask): Ansible tasks.
    """
    tasks = []

    tasks.extend(_download_fortishield_package(package_url, package_destination))

    tasks.append(
        AnsibleTask({
            'name': 'Upgrade fortishield RPM package',
            'become': True,
            'shell': f"yum install -y {package_name}",
            'args': {
                'chdir': package_destination
            },
            'register': 'rpm_upgrade',
            'retries': 6,
            'delay': 10,
            'until': 'rpm_upgrade is success',
        })
    )

    return tasks


def _upgrade_fortishield_deb(package_name, package_url, package_destination):
    """Ansible tasks to upgrade a fortishield DEB package.

    Args:
        package_name (str): Name of the package to be installed.
        package_url (str): URL of the package to be installed.
        package_destination (str): Destination folder where the package will be downloaded.

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    tasks = []

    tasks.extend(_download_fortishield_package(package_url, package_destination))

    tasks.append(
        AnsibleTask({
            'name': 'Upgrade fortishield DEB package',
            'become': True,
            'apt': {
                'deb': f"{package_destination}/{package_name}",
            },
            'register': 'deb_upgrade',
            'retries': 6,
            'delay': 10,
            'until': 'deb_upgrade is success',
        })
    )

    return tasks


def _uninstall_fortishield_rpm(fortishield_target):
    """Ansible tasks to uninstall a fortishield RPM package.

    Args:
        fortishield_target (str): Fortishield target [manager or agent].

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    tasks = [
        AnsibleTask({
            'name': 'Uninstall fortishield RPM package',
            'become': True,
            'shell': f"yum remove -y fortishield-{fortishield_target}",
        })
    ]

    tasks.extend(_delete_files(['/var/ossec']))

    return tasks


def _uninstall_fortishield_deb(fortishield_target):
    """Ansible tasks to uninstall a fortishield DEB package.

    Args:
        fortishield_target (str): Fortishield target [manager or agent].

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': 'Uninstall fortishield DEB package',
            'become': True,
            'apt': {
                'name': f"fortishield-{fortishield_target}",
                'state': 'absent',
                'purge': True
            }
        })
    ]


def _run_linux_commands(commands):
    """Ansible tasks to run linux commands.

    Args:
        commands (list(str)): Commands to run with the playbook. [command1, command2, ...]

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
       AnsibleTask({
           'name': f"Run Command {command}",
           'shell': command
        }) for command in commands
    ]


def _download_files(files_data):
    """Ansible tasks to download files.

    Args:
        files_data (list(dict)): URL and download destination info. [{url: destination}, ...]

    Returns:
       list(AnsibleTask): Ansible tasks.
    """
    return [
       AnsibleTask({
            'name': f"Download_file {file_url}",
            'get_url': {
                'url': file_url,
                'dest': file_destination,
                'mode': '0755'
            },
            'register': 'download_file',
            'retries': 3,
            'delay': 10,
            'until': 'download_file is success'
        }) for file_url, file_destination in files_data.items()
    ]


def _fetch_files(files_data):
    """Ansible tasks to fetch remote files to a local path.

    Args:
        files_data (list(dict)): Source and destination data. [{remote_src: local_destination}, ...]

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
       AnsibleTask({
            'name': f"Fetch {remote_file_path} from remote path to {local_file_path} local path",
            'fetch': {
                'src': remote_file_path,
                'dest': local_file_path,
                'flat': 'yes'
            }
        }) for remote_file_path, local_file_path in files_data.items()
    ]


def _delete_files(files_path):
    """Ansible tasks to delete files.

    Args:
        files_path (list(str)): List of files path to delete. [file_path1, file_path2, ...]

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': f"Delete {item}",
            'become': True,
            'file': {
                'state': 'absent',
                'path': item
            }
        }) for item in files_path
    ]


def _wait_seconds(num_seconds):
    """Ansible tasks to wait for the indicated time.

    Args:
        num_seconds (int): Number of seconds to wait.

    Returns:
        list(AnsibleTask): Ansible tasks.
    """
    return [
        AnsibleTask({
            'name': f"Wait {num_seconds} seconds",
            'pause': {
                'seconds': num_seconds,
            }
        })
    ]
