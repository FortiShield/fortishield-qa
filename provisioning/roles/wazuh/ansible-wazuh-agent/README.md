Ansible Playbook - Fortishield agent
==============================

This role will install and configure a Fortishield Agent.

OS Requirements
----------------

This role is compatible with:
 * Red Hat
 * CentOS
 * Fedora
 * Debian
 * Ubuntu


Role Variables
--------------

* `fortishield_managers`: Collection of Fortishield Managers' IP address, port, and protocol used by the agent
* `fortishield_agent_authd`: Collection with the settings to register an agent using authd.

Playbook example
----------------

The following is an example of how this role can be used:

     - hosts: all:!fortishield-manager
       roles:
         - ansible-fortishield-agent
       vars:
         fortishield_managers:
           - address: 127.0.0.1
             port: 1514
             protocol: tcp
             api_port: 55000
             api_proto: 'http'
             api_user: 'ansible'
         fortishield_agent_authd:
           registration_address: 127.0.0.1
           enable: true
           port: 1515
           ssl_agent_ca: null
           ssl_auto_negotiate: 'no'


License and copyright
---------------------

FORTISHIELD Copyright (C) 2016, Fortishield Inc. (License GPLv3)

### Based on previous work from dj-wasabi

  - https://github.com/dj-wasabi/ansible-ossec-server

### Modified by Fortishield

The playbooks have been modified by Fortishield, including some specific requirements, templates and configuration to improve integration with Fortishield ecosystem.
