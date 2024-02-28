import os
from pathlib import Path

from fortishield_testing.qa_ctl.provisioning.fortishield_deployment.fortishield_package import FortishieldPackage
from fortishield_testing.qa_ctl.provisioning.ansible.ansible_task import AnsibleTask
from fortishield_testing.qa_ctl import QACTL_LOGGER
from fortishield_testing.tools.logging import Logging


class FortishieldLocalPackage(FortishieldPackage):
    """Install Fortishield from a local existent package

    Args:
        fortishield_target (string): Type of the Fortishield instance desired (agent or manager).
        installation_files_path (string): Path where is located the Fortishield instalation files.
        local_package_path (string): Path where the local package is located.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        version (string): The version of Fortishield. Parameter set by default to 'None'.
        system (string): System of the Fortishield installation files. Parameter set by default to 'None'.

    Attributes:
        local_package_path (string): Path where the local package is located.
        package_name (string): name of the Fortishield package.
        installation_files_path (string): Path where the Fortishield installation files are located.
        local_package_path (string): Path where the local package is located.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
    """
    LOGGER = Logging.get_logger(QACTL_LOGGER)

    def __init__(self, fortishield_target, installation_files_path, local_package_path, qa_ctl_configuration, version=None,
                 system=None):
        self.local_package_path = local_package_path
        self.package_name = Path(self.local_package_path).name
        super().__init__(fortishield_target=fortishield_target, installation_files_path=installation_files_path, version=version,
                         system=system, qa_ctl_configuration=qa_ctl_configuration)

    def download_installation_files(self, inventory_file_path, hosts='all'):
        """Download the installation files of Fortishield in the given inventory file path

        Args:
            inventory_file_path (string): path where the instalation files are going to be stored.
            hosts (string): Parameter set to `all` by default.

        Returns:
            str: String with the complete path of the installation package
        """
        FortishieldLocalPackage.LOGGER.debug(f"Copying local package {self.local_package_path} to "
                                       f"{self.installation_files_path} in {hosts} hosts")

        copy_ansible_task = AnsibleTask({
            'name': f"Copy {self.local_package_path} package to {self.installation_files_path}",
            'copy': {'src': self.local_package_path, 'dest': self.installation_files_path}
        })

        FortishieldLocalPackage.LOGGER.debug(f"{self.local_package_path} has been successfully copied in {hosts} hosts")

        super().download_installation_files(inventory_file_path, [copy_ansible_task], hosts)

        return os.path.join(self.installation_files_path, self.package_name)
