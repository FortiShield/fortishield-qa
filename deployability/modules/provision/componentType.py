

class ComponentType:
    """
    Class to define the type of component to be provisioned
    """
    def __init__(self, component_info):
        self.component = component_info.component
        self.type = component_info.type
        self.live = component_info.live
        self.version = component_info.version
        self.manager_ip = component_info.manager_ip or None

    def get_templates_path(self, action):
        """
        Get the path to the templates.
        """
        pass

    def get_templates_order(self, action):
        """
        Get the order of the templates to be executed.
        """
        pass

    def generate_dict(self):
        """
        Generate the dictionary with the variables to be used to render the templates.
        """
        variables = {
                    'component': self.component,
                    'version': self.version,
                    'live': self.live,
                    'manager_ip': self.manager_ip,
                    'templates_path': self.templates_path,
                    'templates_order': self.templates_order or None
                }

        return variables

class Package(ComponentType):
    """
    Class to define the type of package to be provisioned
    """
    TEMPLATE_BASE_PATH = 'provision/wazuh'

    def __init__(self, component_info, action):
        super().__init__(component_info)
        self.templates_path = f'{self.TEMPLATE_BASE_PATH}/{self.type}/{action}'
        self.templates_order = self.get_templates_order(action)
        self.variables_dict = self.generate_dict()

    def get_templates_order(self, action):
        if action == "install":
            return ["set_repo.j2", "install.j2", "register.j2", "service.j2"]
        return []

class AIO(ComponentType):
    """
    Class to define the type of AIO to be provisioned
    """
    TEMPLATE_BASE_PATH = 'provision/wazuh'

    def __init__(self, component_info, action):
        super().__init__(component_info)
        self.templates_path = f'{self.TEMPLATE_BASE_PATH}/{self.type}/{action}'
        self.templates_order = self.get_templates_order(action)
        self.version_mayor_minor = self.version.split('.')[0] + '.' + self.version.split('.')[1]
        self.variables_dict = self.generate_dict()

    def generate_dict(self):
        """
        Generate the dictionary with the variables to be used to render the templates.
        """
        variables = super().generate_dict()
        variables['version_mayor_minor'] = self.version_mayor_minor
        return variables

    def get_templates_order(self, action):
        return ["download.j2", f"{action}.j2"]

class Generic(ComponentType):
    """
    Class to define the type of generic component to be provisioned
    """
    TEMPLATE_BASE_PATH = 'provision/generic'

    def __init__(self, component_info, action):
        super().__init__(component_info)
        self.templates_path = f'{self.TEMPLATE_BASE_PATH}/{action}'
        self.templates_order = self.get_templates_order(action)
        self.variables_dict = self.generate_dict()

    def get_templates_order(self, action):
        return []

class Dependencies(ComponentType):
    """
    Class to define the type of dependencies to be provisioned
    """
    TEMPLATE_BASE_PATH = 'provision/deps'

    def __init__(self, component_info, action):
        super().__init__(component_info)
        self.templates_path = f'{self.TEMPLATE_BASE_PATH}'
        self.templates_order = self.get_templates_order(action)
        self.variables_dict = self.generate_dict()

    def get_templates_order(self, action):
        return []
