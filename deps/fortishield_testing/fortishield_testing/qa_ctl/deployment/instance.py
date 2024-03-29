# Copyright (C) 2015-2021, Fortishield Inc.
# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
from abc import ABC, abstractmethod


class Instance(ABC):
    """Abstract class to hold common methods for instance handling"""
    @abstractmethod
    def run(self):
        """Method to start the instance."""

    @abstractmethod
    def restart(self):
        """Method to restart the instance."""

    @abstractmethod
    def halt(self):
        """Method to stop the instance."""

    @abstractmethod
    def destroy(self):
        """Method to destroy the instance."""

    @abstractmethod
    def get_instance_info(self):
        """Method to get the instance information."""

    @abstractmethod
    def get_name(self):
        """Method to get the instance name."""

    @abstractmethod
    def status(self):
        """Method to get the instance status."""
