from pathlib import Path
from abc import ABC, abstractmethod

import yaml

from ..credentials.base import Credentials
from ..models import Instance, InstanceParams

TEMPLATES_DIR = Path(__file__).parent / 'templates'
SPECS_DIR = Path(__file__).parent / 'specs'
OS_PATH = SPECS_DIR / 'os.yml'
ROLES_PATH = SPECS_DIR / 'roles.yml'

class Provider():

    def __init__(self):
        # self.credential = None
        self.working_dir = Path()
        self.instance: Instance = None

    @abstractmethod
    def create(self):
        raise NotImplementedError()

    @abstractmethod
    def start(self):
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        raise NotImplementedError()

    @abstractmethod
    def delete(self):
        raise NotImplementedError()

    @abstractmethod
    def status(self):
        raise NotImplementedError()

    @abstractmethod
    def get_ansible_inventory(self):
        raise NotImplementedError()

    def _get_os_specs(self, provider: str) -> dict:
        with open(OS_PATH, "r") as f:
            return yaml.safe_load(f).get(provider)

    def _get_role_specs(self, provider: str) -> dict:
        with open(ROLES_PATH, "r") as f:
            return yaml.safe_load(f).get(provider)
