import argparse
import subprocess
import os
import sys

# ---------------- Methods ---------------------

def run(ansible, inventory):
  status = {}
  current_dir = os.path.abspath(os.getcwd())
  for host in inventory['all']['hosts']:

    packages = inventory['all']['hosts'][host].get('install')
    distribution = inventory['all']['hosts'][host].get('distribution')
    remote_user = inventory['all']['hosts'][host].get('ansible_user')
    private_key = inventory['all']['hosts'][host].get('ansible_ssh_private_key_file')
    remote_port = inventory['all']['hosts'][host].get('ansible_port')

    for item in packages:
      if isinstance(item, dict):
          type = item.get('type')
          package = item.get('component')
      else:
          type = None
          package = item

      if "wazuh" in package and type is not None:
        extraVars = ""
        if "wazuh-agent" in package:
          if inventory['all']['hosts'][host].get('manager') is not None:
            extraVars = {
              "manager_ip": {inventory['all']['hosts'][host].get('manager')}
            }
        if "package" in type or "wazuh-agent" in package:
          if distribution == 'debian':
            path = current_dir + "/playbooks/provision/package/deb"
            ansible.set_path(path)
          if distribution == 'rpm':
            path = current_dir + "/playbooks/provision/package/rpm"
            ansible.set_path(path)

          results = ansible.run_playbook("set_repo.yml")
          status.update(results.stats)
          results = ansible.run_playbook("install.yml")
          status.update(results.stats)
          results = ansible.run_playbook("register.yml", extraVars)
          status.update(results.stats)
          results = ansible.run_playbook("service.yml")
          status.update(results.stats)
        elif "aio" in type:
          path = "playbooks/provision/aio"
          ansible.set_path(path)
          extraVars = {
            "version": "4.6",
            "name": host,
            "component": package
          }

          results = ansible.run_playbook("download.yml", extraVars)
          status.update(results.stats)
          results = ansible.run_playbook("install.yml", extraVars)
          status.update(results.stats)

      else:
        pkg_manager = ""

        if distribution == 'debian':
          pkg_manager = 'apt'
        if distribution == 'rpm':
          pkg_manager = 'yum'

        install_playbook = {
          'name': 'Install packages on ' + host,
          'hosts': host,
          'remote_user': remote_user,
          'port': remote_port,
          'vars': {
            'ansible_ssh_private_key_file': private_key
          },
          'tasks': [
            {
                'name': 'Install' + package,
                pkg_manager: {
                    'name': package,
                    'state': 'present'
                },
                'become': True
            }
          ]
        }

        results = ansible.run_playbook(install_playbook)
        status.update(results.stats)

  print("Resume")
  print(status)

# ----------------------------------------------


# ----------------------------------------------

def install_dependencies():
  venv_path = 'venv'
  if not os.path.exists(venv_path):
      subprocess.run(['python3', '-m', 'venv', venv_path], check=True)
  activate_script = os.path.join(venv_path, 'bin', 'activate')
  activate_command = f"source {activate_script}" if sys.platform != 'win32' else f"call {activate_script}"
  subprocess.run(activate_command, shell=True)
  subprocess.run(['python3', '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
  subprocess.run(['pip', 'install', '-r', 'utils/requirements.txt'], check=True)


# ----------------------------------------------

def main(inventory_file):

  install_dependencies()

  project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
  sys.path.append(project_root)

  import src.classes.Ansible as Ansible

  ansible = Ansible.Ansible(inventory_file)
  inventory = ansible.get_inventory()

  run(ansible, inventory)

# ---------------- Main ---------------------

if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--inventory", help="Archivo YAML de inventario de Ansible")
  args = parser.parse_args()

  main(args.inventory)