import src.classes.Ansible as Ansible
import time # Remove in PR

def main():

    # -------------------
    # Vars
    # -------------------

    # General
    inventory = "inventory.yaml"
    playbook_path = "/home/nonsatus/Documents/Wazuh/Repositories/wazuh-qa/4524/playbooks"

    # Provision
    playbook_provision_repo = "provision/set_repo.yml"
    playbook_provision_install = "provision/install.yml"
    playbook_provision_register = "provision/register.yml"
    playbook_provision_service = "provision/service.yml"

    # Test
    playbook_test_repo = "tests/test_repo.yml"
    playbook_test_provision = "tests/provision_test.yml"
    playbook_test_install = "tests/test_install.yml"

    # Extra data
    live = True
    version = '4.5.2'
    if live:
        branch_version = "v" + version
    extra_vars = {
        'version': version,
        'branch_version': branch_version
    }

    # -------------------
    # Tasks
    # -------------------

    ansible = Ansible.Ansible(playbook_path)
    ansible.set_inventory(inventory)

    # Provision stage

    #ansible.run_playbook(playbook_provision_repo)
    #ansible.run_playbook(playbook_provision_install)
    #ansible.run_playbook(playbook_provision_register)
    #ansible.run_playbook(playbook_provision_service)

    time.sleep(20) # Agent must connect to manager. Remove in PR

    # Test stage

    # Run tests in endpoints

    ansible.run_playbook(playbook_test_provision)

    ansible.run_playbook(playbook_test_repo)
    ansible.run_playbook(playbook_test_install, extra_vars)
    #ansible.run_playbook(playbook_test_register)
    #ansible.run_playbook(playbook_test_service)


    #ansible.run_playbook(playbook_test_install, 'Agent*', extra_vars)
    #ansible.run_playbook(playbook_test_install, 'Manager*', extra_vars)

    #clear = "clear.yml"
    #ansible.run_playbook(clear)


    # -------------------


if __name__ == "__main__":
    main()