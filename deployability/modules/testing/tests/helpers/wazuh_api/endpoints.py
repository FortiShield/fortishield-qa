#   - Wazuh API endpoints

# -- Root --
API_ROOT = '/'

# -- Security --
SECURITY = '/security'
# Users
SECURITY_USER = f'{SECURITY}/user'
SECURITY_USERS = f'{SECURITY}/users'
# Authentication
SECURITY_AUTHENTICATE = f'{SECURITY_USER}/authenticate'
# Configuration
SECURITY_CONFIG = f'{SECURITY}/config'

# -- Groups --
GROUPS = '/groups'

# -- Agents --
AGENTS = '/agents'
AGENTS_GROUP = f'{AGENTS}/group'

# -- Manager --
MANAGER = '/manager'
MANAGER_STATUS = f'{MANAGER}/status'
MANAGER_INFO = f'{MANAGER}/info'
MANAGER_CONFIGURATION = f'{MANAGER}/configuration'