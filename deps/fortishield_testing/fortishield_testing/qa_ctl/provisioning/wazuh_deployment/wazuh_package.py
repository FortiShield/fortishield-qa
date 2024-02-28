from abc import ABC, abstractmethod

from fortishield_testing.qa_ctl.provisioning.fortishield_deployment.fortishield_installation import FortishieldInstallation


class FortishieldPackage(FortishieldInstallation, ABC):
    """Install Fortishield from the given sources. In this case, the installation
        will be done from a package file.

    Args:
        version (string): The version of Fortishield.
        system (string): System of the Fortishield installation files.
        fortishield_target (string): Type of the Fortishield instance desired (agent or manager).
        installation_files_path (string): Path where is located the Fortishield instalation files.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.

    Attributes:
        version (string): The version of Fortishield.
        system (string): System of the Fortishield installation files.
        fortishield_target (string): Type of the Fortishield instance desired (agent or manager).
        installation_files_path (string): Path where is located the Fortishield instalation files.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
    """
    def __init__(self, version, system, fortishield_target, installation_files_path, qa_ctl_configuration):
        self.version = version
        self.system = system
        super().__init__(fortishield_target=fortishield_target, installation_files_path=installation_files_path,
                         qa_ctl_configuration=qa_ctl_configuration)

    @abstractmethod
    def download_installation_files(self, inventory_file_path, ansible_tasks, hosts='all'):
        """Download the installation files of Fortishield.

        Args:
            inventory_file_path (string): path where the instalation files are going to be stored
            ansible_tasks (ansible object): ansible instance with already provided tasks to run
            hosts (string): Parameter set to `all` by default
        """
        super().download_installation_files(inventory_file_path, ansible_tasks, hosts)
