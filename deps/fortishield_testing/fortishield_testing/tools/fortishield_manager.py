import os
import subprocess
import requests
from fortishield_testing.tools import FORTISHIELD_PATH
from fortishield_testing.fortishield_db import query_wdb
from fortishield_testing.api import get_api_details_dict


def list_agents_ids():
    fortishielddb_result = query_wdb('global get-all-agents last_id -1')
    list_agents = [agent['id'] for agent in fortishielddb_result if not (0 == agent.get('id'))]

    return list_agents


def remove_agents(agents_id, remove_type='fortishielddb'):
    if remove_type not in ['fortishielddb', 'manage_agents', 'api']:
        raise ValueError("Invalid type of agent removal: %s" % remove_type)

    if agents_id:
        for agent_id in agents_id:
            if remove_type == 'manage_agents':
                subprocess.call([f"{FORTISHIELD_PATH}/bin/manage_agents", "-r", f"{agent_id}"], stdout=open(os.devnull, "w"),
                                stderr=subprocess.STDOUT)
            elif remove_type == 'fortishielddb':
                result = query_wdb(f"global delete-agent {str(agent_id)}")
        if remove_type == 'api':
            api_details = get_api_details_dict()
            payload = {
                'agents_list': agents_id,
                'status': 'all',
                'older_than': '0s'
            }
            url = f"{api_details['base_url']}/agents"
            response = requests.delete(url, headers=api_details['auth_headers'], params=payload, verify=False)
            response_data = response.json()
            if response.status_code != 200:
                raise RuntimeError(f"Error deleting an agent: {response_data}")


def remove_all_agents(remove_type):
    remove_agents(list_agents_ids(), remove_type)


def create_group(group):
    """Create group with /var/ossec/bin/agent_groups

    Args:
        group (str): Group name

    Returns:
        result(str): Return code
    """
    result = subprocess.run([f'{FORTISHIELD_PATH}/bin/agent_groups', '-a', '-q', '-g', f'{group}']).returncode

    return result


def delete_group(group):
    """Delete group with /var/ossec/bin/agent_groups

    Args:
        group (str): Group name

    Returns:
        result(str): Return code
    """
    result = subprocess.run([f'{FORTISHIELD_PATH}/bin/agent_groups', '-r', '-q', '-g', f'{group}']).returncode

    return result
