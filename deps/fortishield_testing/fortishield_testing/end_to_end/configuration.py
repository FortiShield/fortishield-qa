"""
Module for change configurations of remote hosts.
----------------------------------------

This module provides functions for configuring and managing remote host
configurations using the HostManager class and related tools.

Functions:
    - backup_configurations: Backup configurations for all hosts in the specified host manager.
    - restore_configuration: Restore configurations for all hosts in the specified host manager.
    - configure_host: Configure a specific host.
    - configure_environment: Configure the environment for all hosts in the specified host manager.


Copyright (C) 2015, Fortishield Inc.
Created by Fortishield, Inc. <security@khulnasoft.com>.
This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2
"""
import xml.dom.minidom
import logging

from multiprocessing.pool import ThreadPool
from typing import Dict, List

from fortishield_testing.end_to_end import configuration_filepath_os
from fortishield_testing.tools.configuration import set_section_fortishield_conf
from fortishield_testing.tools.system import HostManager


def backup_configurations(host_manager: HostManager) -> Dict[str, str]:
    """
    Backup configurations for all hosts in the specified host manager.

    Args:
        host_manager: An instance of the HostManager class containing information about hosts.

    Returns:
        dict: A dictionary mapping host names to their configurations.

    Example of returned dictionary:
        {
            'manager': '<ossec_config>...</ossec_config>',
            'agent1': ...
        }
    """
    logging.info("Backing up configurations")
    backup_configurations = {}
    for host in host_manager.get_group_hosts('all'):
        host_os_name = host_manager.get_host_variables(host)['os_name']
        configuration_filepath = configuration_filepath_os[host_os_name]

        backup_configurations[host] = host_manager.get_file_content(str(host),
                                                                    configuration_filepath)
    logging.info("Configurations backed up")
    return backup_configurations


def restore_configuration(host_manager: HostManager, configuration: Dict[str, List]) -> None:
    """
    Restore configurations for all hosts in the specified host manager.

    Args:
        host_manager: An instance of the HostManager class containing information about hosts.
        configuration: A dictionary mapping host names to their configurations.

    Example of configuration dictionary:
        {
            'manager': '<ossec_config>...</ossec_config>',
            'agent1': ...
        }
    """
    logging.info("Restoring configurations")
    for host in host_manager.get_group_hosts('all'):
        host_os_name = host_manager.get_host_variables(host)['os_name']
        configuration_filepath = configuration_filepath_os[host_os_name]

        host_manager.modify_file_content(host, configuration_filepath, configuration[host])
    logging.info("Configurations restored")


def configure_host(host: str, host_configuration: Dict[str, Dict], host_manager: HostManager) -> None:
    """
    Configure a specific host.

    Args:
        host: The name of the host to be configured.
        host_configuration: Role of the configured host for the host. Check below for example.
        host_manager: An instance of the HostManager class containing information about hosts.

    Note: The host_configuration dictionary must contain a list of sections and elements to be configured. The sections
    not included in the dictionary will not be modified maintaining the current configuration.


    Example of host_configuration dictionary:
        {
           "manager1":[
              {
                 "sections":[
                    {
                       "section":"vulnerability-detection",
                       "elements":[
                          {
                             "enabled":{
                                "value":"yes"
                             }
                          },
                          {
                             "index-status":{
                                "value":"yes"
                             }
                          },
                          {
                             "feed-update-interval":{
                                "value":"2h"
                             }
                          }
                       ]
                    },
             ],
             "metadata":{}
            }
            ],
        }
    """
    logging.info(f"Configuring host {host}")

    host_os = host_manager.get_host_variables(host)['os_name']
    config_file_path = configuration_filepath_os[host_os]

    host_config = host_configuration.get(host)

    if not host_config:
        raise TypeError(f"Host {host} configuration does not include a valid role (manager or agent):"
                        f"{host_configuration}")

    current_config = host_manager.get_file_content(str(host), config_file_path)

    # Extract the sections from the first element of host_config

    sections = host_config[0].get('sections')

    # Combine the current hos configuration and the desired configuration
    new_config_unformatted = set_section_fortishield_conf(sections, current_config.split("\n"))

    # Format new configuration
    new_config_formatted_xml = xml.dom.minidom.parseString(''.join(new_config_unformatted))

    # Get rid of the first no expected XML version line
    new_config_formatted_xml = new_config_formatted_xml.toprettyxml().split("\n")[1:]

    final_configuration = "\n".join(new_config_formatted_xml)

    host_manager.modify_file_content(str(host), config_file_path, final_configuration)

    logging.info(f"Host {host} configured")


def configure_environment(host_manager: HostManager, configurations: Dict[str, List]) -> None:
    """
    Configure the environment for all hosts in the specified host manager.

    Args:
        host_manager: An instance of the HostManager class containing information about hosts.
        configurations: A dictionary mapping host roles to their configuration details.

    Example of host_configurations dictionary:
        {
           "manager1":[
              {
                 "sections":[
                    {
                       "section":"vulnerability-detection",
                       "elements":[
                          {
                             "enabled":{
                                "value":"yes"
                             }
                          },
                          {
                             "index-status":{
                                "value":"yes"
                             }
                          },
                          {
                             "feed-update-interval":{
                                "value":"2h"
                             }
                          }
                       ]
                    },
             ],
             "metadata":{}
            }
            ],
        }
    """
    logging.info("Configuring environment")
    configure_environment_parallel_map = [(host, configurations) for host in host_manager.get_group_hosts('all')]

    with ThreadPool() as pool:
        pool.starmap(configure_host,
                     [(host, config, host_manager) for host, config in configure_environment_parallel_map])

    logging.info("Environment configured")
