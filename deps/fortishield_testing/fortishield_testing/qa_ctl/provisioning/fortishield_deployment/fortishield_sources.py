from fortishield_testing.qa_ctl.provisioning.fortishield_deployment.fortishield_installation import FortishieldInstallation
from fortishield_testing.qa_ctl.provisioning.ansible.ansible_task import AnsibleTask
from fortishield_testing.qa_ctl import QACTL_LOGGER
from fortishield_testing.tools.logging import Logging


class FortishieldSources(FortishieldInstallation):
    """Install Fortishield from the given sources. In this case, the installation
        will be done from the source files of a repository.

    Args:
        fortishield_target (string): Type of the Fortishield instance desired (agent or manager).
        installation_files_path (string): Path where is located the Fortishield instalation files.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        fortishield_branch (string): String containing the branch from where the files are going to be downloaded.
        This field is set to 'master' by default.
        fortishield_repository_url (string): URL from the repo where the fortishield sources files are located.
        This parameter is set to 'https://github.com/fortishield/fortishield.git' by default.

    Attributes:
        fortishield_target (string): Type of the Fortishield instance desired (agent or manager).
        installation_files_path (string): Path where is located the Fortishield instalation files.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        fortishield_branch (string): String containing the branch from where the files are going to be downloaded.
        This field is set to 'master' by default.
        fortishield_repository_url (string): URL from the repo where the fortishield sources files are located.
        This parameter is set to 'https://github.com/fortishield/fortishield.git' by default.
    """
    LOGGER = Logging.get_logger(QACTL_LOGGER)

    def __init__(self, fortishield_target, installation_files_path, qa_ctl_configuration, fortishield_branch='master',
                 fortishield_repository_url='https://github.com/fortishield/fortishield.git'):
        self.fortishield_branch = fortishield_branch
        self.fortishield_repository_url = fortishield_repository_url
        super().__init__(fortishield_target=fortishield_target, qa_ctl_configuration=qa_ctl_configuration,
                         installation_files_path=f"{installation_files_path}/fortishield-{self.fortishield_branch}")

    def download_installation_files(self, inventory_file_path, hosts='all'):
        """Download the source files of Fortishield using an AnsibleTask instance.

        Args:
            inventory_file_path (string): path where the instalation files are going to be stored
            hosts (string): Parameter set to `all` by default

        Returns:
            str: String with the path where the installation files are located
        """
        FortishieldSources.LOGGER.debug(f"Downloading Fortishield sources from {self.fortishield_branch} branch in {hosts} hosts")

        download_fortishield_sources_task = AnsibleTask({
            'name': f"Download Fortishield branch in {self.installation_files_path}",
            'shell': f"cd {self.installation_files_path} && curl -Ls https://github.com/fortishield/fortishield/archive/"
                     f"{self.fortishield_branch}.tar.gz | tar zx && mv fortishield-*/* ."
        })
        FortishieldSources.LOGGER.debug(f"Fortishield sources from {self.fortishield_branch} branch were successfully downloaded in "
                                  f"{hosts} hosts")
        super().download_installation_files(inventory_file_path, [download_fortishield_sources_task], hosts)

        return self.installation_files_path
