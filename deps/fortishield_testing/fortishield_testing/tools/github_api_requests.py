import requests


OWNER = 'fortishield'
FORTISHIELD_REPO = 'fortishield'
FORTISHIELD_QA_REPO = 'fortishield-qa'
GITHUB_API_URL = 'https://api.github.com'
HEADERS = {'Accept': 'application/vnd.github.v3+json'}
EXTRA_ARGS = '?per_page=100'


def _run_get_request(request_url, headers):
    response = requests.get(f"{GITHUB_API_URL}{request_url}", headers=headers)
    status_code = response.status_code

    if status_code != 200:
        raise ValueError(f"Could not run the GET request to {GITHUB_API_URL}/{request_url}. Status code {status_code}")

    all_data = response.json()

    while 'next' in response.links.keys():
        response = requests.get(response.links['next']['url'], headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Could not run the GET request to {GITHUB_API_URL}/{request_url}. Status "
                             f"code {response.status_code}")
        all_data.extend(response.json())

    return all_data


def _get_request_data(url, field_name):
    data = _run_get_request(url, HEADERS)

    return [item[field_name] for item in data]


def get_fortishield_tags():
    return _get_request_data(f"/repos/{OWNER}/{FORTISHIELD_REPO}/tags{EXTRA_ARGS}", 'name')


def get_fortishield_releases():
    return _get_request_data(f"/repos/{OWNER}/{FORTISHIELD_REPO}/releases{EXTRA_ARGS}", 'tag_name')


def get_fortishield_master_version():
    response = requests.get('https://raw.githubusercontent.com/fortishield/fortishield/master/src/VERSION')

    return (response.text).split('\n')[0].replace('v', '')


def get_fortishield_qa_master_version():
    response = requests.get('https://raw.githubusercontent.com/fortishield/fortishield-qa/master/version.json')

    return response.json()['version'].replace('v', '')


def version_is_released(version):
    releases = get_fortishield_releases()
    v_version = f"v{version}" if not 'v' in version else version

    return v_version in releases


def branch_exist(branch_name, repository=FORTISHIELD_REPO):
    branches = get_branches(repository)

    return branch_name in branches


def get_branches(repository=FORTISHIELD_REPO):
    return _get_request_data(f"/repos/{OWNER}/{repository}/branches{EXTRA_ARGS}", 'name')


def get_last_fortishield_version():
    return get_fortishield_releases()[0]
