# Copyright (C) 2015-2022, Fortishield Inc.
# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import os
import platform
import subprocess
import sys


if sys.platform == 'win32':
    FORTISHIELD_PATH = os.path.join("C:", os.sep, "Program Files (x86)", "ossec-agent")
    FORTISHIELD_CONF = os.path.join(FORTISHIELD_PATH, 'ossec.conf')
    FORTISHIELD_LOCAL_INTERNAL_OPTIONS = os.path.join(FORTISHIELD_PATH, 'local_internal_options.conf')
    FORTISHIELD_SOURCES = os.path.join('/', 'fortishield')
    AGENT_CONF = os.path.join(FORTISHIELD_PATH, 'shared', 'agent.conf')
    LOG_FILE_PATH = os.path.join(FORTISHIELD_PATH, 'ossec.log')
    CLIENT_KEYS_PATH = os.path.join(FORTISHIELD_PATH, 'client.keys')
    PREFIX = os.path.join('c:', os.sep)
    GEN_OSSEC = None
    FORTISHIELD_API_CONF = None
    FORTISHIELD_SECURITY_CONF = None
    API_LOG_FILE_PATH = None
    API_JSON_LOG_FILE_PATH = None
    API_LOG_FOLDER = None
    AGENT_STATISTICS_FILE = os.path.join(FORTISHIELD_PATH, 'fortishield-agent.state')
    LOGCOLLECTOR_STATISTICS_FILE = os.path.join(FORTISHIELD_PATH, 'fortishield-logcollector.state')
    REMOTE_STATISTICS_FILE = None
    ANALYSIS_STATISTICS_FILE = None
    UPGRADE_PATH = os.path.join(FORTISHIELD_PATH, 'upgrade')
    AGENT_AUTH_BINARY_PATH = os.path.join(FORTISHIELD_PATH, 'agent-auth.exe')
    ANALYSISD_BINARY_PATH = None
    HOSTS_FILE_PATH = os.path.join("C:", os.sep, "Windows", "System32", "drivers", "etc", "hosts")
    GLOBAL_DB_PATH = None
    FORTISHIELD_UNIX_USER = 'fortishield'
    FORTISHIELD_UNIX_GROUP = 'fortishield'
    GLOBAL_DB_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'db', 'global.db')
    ARCHIVES_LOG_FILE_PATH = os.path.join(FORTISHIELD_PATH, 'logs', 'archives', 'archives.log')
    ACTIVE_RESPONSE_BINARY_PATH = os.path.join(FORTISHIELD_PATH, 'active-response', 'bin')
else:
    FORTISHIELD_SOURCES = os.path.join('/', 'fortishield')

    FORTISHIELD_UNIX_USER = 'fortishield'
    FORTISHIELD_UNIX_GROUP = 'fortishield'

    if sys.platform == 'darwin':
        FORTISHIELD_PATH = os.path.join("/", "Library", "Ossec")
        PREFIX = os.path.join('/', 'private', 'var', 'root')
        GEN_OSSEC = None
    else:
        FORTISHIELD_PATH = os.path.join("/", "var", "ossec")
        GEN_OSSEC = os.path.join(FORTISHIELD_SOURCES, 'gen_ossec.sh')
        PREFIX = os.sep

    FORTISHIELD_CONF_RELATIVE = os.path.join('etc', 'ossec.conf')
    FORTISHIELD_LOCAL_INTERNAL_OPTIONS = os.path.join(FORTISHIELD_PATH, 'etc', 'local_internal_options.conf')
    FORTISHIELD_CONF = os.path.join(FORTISHIELD_PATH, FORTISHIELD_CONF_RELATIVE)
    AGENT_CONF = os.path.join(FORTISHIELD_PATH, 'etc', 'shared', 'agent.conf')
    FORTISHIELD_API_CONF = os.path.join(FORTISHIELD_PATH, 'api', 'configuration', 'api.yaml')
    FORTISHIELD_SECURITY_CONF = os.path.join(FORTISHIELD_PATH, 'api', 'configuration', 'security', 'security.yaml')
    LOG_FILE_PATH = os.path.join(FORTISHIELD_PATH, 'logs', 'ossec.log')
    CLIENT_KEYS_PATH = os.path.join(FORTISHIELD_PATH, 'etc', 'client.keys')
    API_LOG_FILE_PATH = os.path.join(FORTISHIELD_PATH, 'logs', 'api.log')
    API_JSON_LOG_FILE_PATH = os.path.join(FORTISHIELD_PATH, 'logs', 'api.json')
    API_LOG_FOLDER = os.path.join(FORTISHIELD_PATH, 'logs', 'api')
    ARCHIVES_LOG_FILE_PATH = os.path.join(FORTISHIELD_PATH, 'logs', 'archives', 'archives.log')
    AGENT_STATISTICS_FILE = os.path.join(FORTISHIELD_PATH, 'var', 'run', 'fortishield-agentd.state')
    LOGCOLLECTOR_STATISTICS_FILE = os.path.join(FORTISHIELD_PATH, 'var', 'run', 'fortishield-logcollector.state')
    LOGCOLLECTOR_FILE_STATUS_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'logcollector', 'file_status.json')
    REMOTE_STATISTICS_FILE = os.path.join(FORTISHIELD_PATH, 'var', 'run', 'fortishield-remoted.state')
    ANALYSIS_STATISTICS_FILE = os.path.join(FORTISHIELD_PATH, 'var', 'run', 'fortishield-analysisd.state')
    UPGRADE_PATH = os.path.join(FORTISHIELD_PATH, 'var', 'upgrade')
    PYTHON_PATH = os.path.join(FORTISHIELD_PATH, 'framework', 'python')
    AGENT_AUTH_BINARY_PATH = os.path.join(FORTISHIELD_PATH, 'bin', 'agent-auth')
    ANALYSISD_BINARY_PATH = os.path.join(FORTISHIELD_PATH, 'bin', 'fortishield-analysisd')
    ACTIVE_RESPONSE_BINARY_PATH = os.path.join(FORTISHIELD_PATH, 'active-response', 'bin')
    AGENT_GROUPS_BINARY_PATH = os.path.join(FORTISHIELD_PATH, 'bin', 'agent_groups')

    if sys.platform == 'sunos5':
        HOSTS_FILE_PATH = os.path.join('/', 'etc', 'inet', 'hosts')
    else:
        HOSTS_FILE_PATH = os.path.join('/', 'etc', 'hosts')
    GLOBAL_DB_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'db', 'global.db')

    try:
        import grp
        import pwd

        FORTISHIELD_UID = pwd.getpwnam(FORTISHIELD_UNIX_USER).pw_uid
        FORTISHIELD_GID = grp.getgrnam(FORTISHIELD_UNIX_GROUP).gr_gid
    except (ImportError, KeyError, ModuleNotFoundError):
        pass


def get_version():

    if platform.system() in ['Windows', 'win32']:
        with open(os.path.join(FORTISHIELD_PATH, 'VERSION'), 'r') as f:
            version = f.read()
            return version[:version.rfind('\n')]

    else:  # Linux, sunos5, darwin, aix...
        return subprocess.check_output([
          f"{FORTISHIELD_PATH}/bin/fortishield-control", "info", "-v"
        ], stderr=subprocess.PIPE).decode('utf-8').rstrip()


def get_service():
    if platform.system() in ['Windows', 'win32']:
        return 'fortishield-agent'

    else:  # Linux, sunos5, darwin, aix...
        service = subprocess.check_output([
          f"{FORTISHIELD_PATH}/bin/fortishield-control", "info", "-t"
        ], stderr=subprocess.PIPE).decode('utf-8').strip()

    return 'fortishield-manager' if service == 'server' else 'fortishield-agent'


_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'data')

CUSTOM_RULES_PATH = os.path.join(FORTISHIELD_PATH, 'etc', 'rules')
LOCAL_RULES_PATH = os.path.join(CUSTOM_RULES_PATH, 'local_rules.xml')
LOCAL_DECODERS_PATH = os.path.join(FORTISHIELD_PATH, 'etc', 'decoders', 'local_decoder.xml')

SERVER_KEY_PATH = os.path.join(FORTISHIELD_PATH, 'etc', 'manager.key')
SERVER_CERT_PATH = os.path.join(FORTISHIELD_PATH, 'etc', 'manager.cert')

CLIENT_CUSTOM_KEYS_PATH = os.path.join(_data_path, 'sslmanager.key')
CLIENT_CUSTOM_CERT_PATH = os.path.join(_data_path, 'sslmanager.cert')

FORTISHIELD_LOGS_PATH = os.path.join(FORTISHIELD_PATH, 'logs')
ALERT_FILE_PATH = os.path.join(FORTISHIELD_LOGS_PATH, 'alerts', 'alerts.json')
ALERT_LOGS_PATH = os.path.join(FORTISHIELD_LOGS_PATH, 'alerts', 'alerts.log')
CLUSTER_LOGS_PATH = os.path.join(FORTISHIELD_LOGS_PATH, 'cluster.log')
QUEUE_SOCKETS_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'sockets')
QUEUE_ALERTS_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'alerts')
QUEUE_DB_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'db')
CLUSTER_SOCKET_PATH = os.path.join(FORTISHIELD_PATH, 'queue', 'cluster')


AGENT_INFO_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, '.agent_info')
ANALYSISD_ANALISIS_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'analysis')
ANALYSISD_QUEUE_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'queue')
AUTHD_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'auth')
EXECD_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'com')
LOGCOLLECTOR_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'logcollector')
LOGTEST_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'logtest')
MONITORD_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'monitor')
REMOTED_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'remote')
SYSCHECKD_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'syscheck')
FORTISHIELD_DB_SOCKET_PATH = os.path.join(QUEUE_DB_PATH, 'wdb')
MODULESD_WMODULES_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'wmodules')
MODULESD_DOWNLOAD_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'download')
MODULESD_CONTROL_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'control')
MODULESD_KREQUEST_SOCKET_PATH = os.path.join(QUEUE_SOCKETS_PATH, 'krequest')
MODULESD_C_INTERNAL_SOCKET_PATH = os.path.join(CLUSTER_SOCKET_PATH, 'c-internal.sock')
ACTIVE_RESPONSE_SOCKET_PATH = os.path.join(QUEUE_ALERTS_PATH, 'ar')

FORTISHIELD_SOCKETS = {
    'fortishield-agentd': [],
    'fortishield-apid': [],
    'fortishield-agentlessd': [],
    'fortishield-csyslogd': [],
    'fortishield-analysisd': [
                        ANALYSISD_ANALISIS_SOCKET_PATH,
                        ANALYSISD_QUEUE_SOCKET_PATH
                       ],
    'fortishield-authd': [AUTHD_SOCKET_PATH],
    'fortishield-execd': [EXECD_SOCKET_PATH],
    'fortishield-logcollector': [LOGCOLLECTOR_SOCKET_PATH],
    'fortishield-monitord': [MONITORD_SOCKET_PATH],
    'fortishield-remoted': [REMOTED_SOCKET_PATH],
    'fortishield-maild': [],
    'fortishield-syscheckd': [SYSCHECKD_SOCKET_PATH],
    'fortishield-db': [FORTISHIELD_DB_SOCKET_PATH],
    'fortishield-modulesd': [
                        MODULESD_WMODULES_SOCKET_PATH,
                        MODULESD_DOWNLOAD_SOCKET_PATH,
                        MODULESD_CONTROL_SOCKET_PATH,
                        MODULESD_KREQUEST_SOCKET_PATH
                      ],
    'fortishield-clusterd': [MODULESD_C_INTERNAL_SOCKET_PATH],
    'fortishield-integratord': []
}

# These sockets do not exist with default Fortishield configuration
FORTISHIELD_OPTIONAL_SOCKETS = [
    MODULESD_KREQUEST_SOCKET_PATH,
    AUTHD_SOCKET_PATH
]

# Fortishield daemons
LOGCOLLECTOR_DAEMON = 'fortishield-logcollector'
AGENTLESS_DAEMON = 'fortishield-agentlessd'
CSYSLOG_DAEMON = 'fortishield-csyslogd'
REMOTE_DAEMON = 'fortishield-remoted'
ANALYSISD_DAEMON = 'fortishield-analysisd'
API_DAEMON = 'fortishield-apid'
MAIL_DAEMON = 'fortishield-maild'
SYSCHECK_DAEMON = 'fortishield-syscheckd'
EXEC_DAEMON = 'fortishield-execd'
MODULES_DAEMON = 'fortishield-modulesd'
CLUSTER_DAEMON = 'fortishield-clusterd'
INTEGRATOR_DAEMON = 'fortishield-integratord'
MONITOR_DAEMON = 'fortishield-monitord'
DB_DAEMON = 'fortishield-db'
AGENT_DAEMON = 'fortishield-agentd'


ALL_MANAGER_DAEMONS = [LOGCOLLECTOR_DAEMON, AGENTLESS_DAEMON, CSYSLOG_DAEMON, REMOTE_DAEMON, ANALYSISD_DAEMON,
                       API_DAEMON, MAIL_DAEMON, SYSCHECK_DAEMON, EXEC_DAEMON, MODULES_DAEMON, CLUSTER_DAEMON,
                       INTEGRATOR_DAEMON, MONITOR_DAEMON, DB_DAEMON]
ALL_AGENT_DAEMONS = [AGENT_DAEMON, EXEC_DAEMON, LOGCOLLECTOR_DAEMON, SYSCHECK_DAEMON, MODULES_DAEMON]
API_DAEMONS_REQUIREMENTS = [API_DAEMON, MODULES_DAEMON, ANALYSISD_DAEMON, EXEC_DAEMON, DB_DAEMON, REMOTE_DAEMON]


DISABLE_MONITORD_ROTATE_LOG_OPTION = {'monitord.rotate_log': '0'}
ANALYSISD_LOCAL_INTERNAL_OPTIONS = {'analysisd.debug': '2'}.update(DISABLE_MONITORD_ROTATE_LOG_OPTION)
AGENTD_LOCAL_INTERNAL_OPTIONS = {'agent.debug': '2', 'execd': '2'}.update(DISABLE_MONITORD_ROTATE_LOG_OPTION)
GCLOUD_LOCAL_INTERNAL_OPTIONS = {'analysisd.debug': '2',
                                 'fortishield_modules.debug': '2'}.update(DISABLE_MONITORD_ROTATE_LOG_OPTION)
LOGTEST_LOCAL_INTERNAL_OPTIONS = {'analysisd.debug': '2'}
REMOTED_LOCAL_INTERNAL_OPTIONS = {'remoted.debug': '2', 'fortishield_database.interval': '2', 'fortishield_db.commit_time': '2',
                                  'fortishield_db.commit_time_max': '3'}.update(DISABLE_MONITORD_ROTATE_LOG_OPTION)
VD_LOCAL_INTERNAL_OPTIONS = {'fortishield_modules.debug': '2'}.update(DISABLE_MONITORD_ROTATE_LOG_OPTION)
WPK_LOCAL_INTERNAL_OPTIONS = {'fortishield_modules.debug': '2'}
