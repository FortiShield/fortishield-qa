import boto3
import fnmatch
import os
from pathlib import Path

from modules.allocation.generic import Provider
from modules.allocation.generic.models import CreationPayload
from modules.allocation.generic.utils import logger
from .credentials import AWSCredentials
from .instance import AWSInstance
from .models import AWSConfig


class AWSProvider(Provider):
    """
    AWSProvider class for managing AWS EC2 instances.
    It inherits from the generic Provider class.

    Attributes:
        provider_name (str): Name of the provider ('aws').
    """

    provider_name = 'aws'

    @classmethod
    def _create_instance(cls, base_dir: Path, params: CreationPayload, config: AWSConfig = None, ssh_key: str = None) -> AWSInstance:
        """
        Create an AWS EC2 instance.

        Args:
            base_dir (Path): Base directory for storing instance data.
            params (CreationPayload): Payload containing creation parameters.
            config (AWSConfig, optional): Configuration for the instance. Defaults to None.
            ssh_key (str, optional): Public or private key for the instance. For example, we assume that if the public key is provided, the private key is located in the same directory and has the same name as the public key. Defaults to None.

        Returns:
            AWSInstance: Created AWSInstance object.
        """
        temp_id = cls._generate_instance_id(cls.provider_name)
        temp_dir = base_dir / temp_id
        credentials = AWSCredentials()
        if not config:
            logger.debug(f"No config provided. Generating from payload")
            # Keys.
            if not ssh_key:
                logger.debug(f"Generating new key pair")
                credentials.generate(temp_dir, temp_id.split('-')[-1] + '_key')
            else:
                logger.debug(f"Using provided key pair")
                key_id = credentials.ssh_key_interpreter(ssh_key)
                credentials.load(key_id)
            # Parse the config if it is not provided.
            config = cls.__parse_config(params, credentials)
        else:
            logger.debug(f"Using provided config")
            # Load the existing credentials.
            credentials.load(config.key_name)
            # Create the temp directory.
            # TODO: Review this on the credentials refactor.
        if not temp_dir.exists():
            logger.debug(f"Creating temp directory: {temp_dir}")
            temp_dir.mkdir(parents=True, exist_ok=True)
        # Generate the instance.
        instance_id = cls.__create_ec2_instance(config)
        # Rename the temp directory to its real name.
        instance_dir = Path(base_dir, instance_id)
        logger.debug(f"Renaming temp {temp_dir} directory to {instance_dir}")
        os.rename(temp_dir, instance_dir)
        if not ssh_key:
            credentials.key_path = (instance_dir / credentials.name)
        else:
            credentials.key_path = (os.path.splitext(ssh_key)[0])

        return AWSInstance(instance_dir, instance_id, credentials, config.user)

    @staticmethod
    def _load_instance(instance_dir: Path, instance_id: str) -> AWSInstance:
        """
        Load an existing AWS EC2 instance.

        Args:
            instance_dir (Path): Directory where instance data is stored.
            instance_id (str): Identifier of the instance.

        Returns:
            AWSInstance: Loaded AWSInstance object.
        """
        return AWSInstance(instance_dir, instance_id)

    @classmethod
    def _destroy_instance(cls, instance_dir: str, identifier: str, key_path: str) -> None:
        """
        Destroy an AWS EC2 instance.

        Args:
            instance_dir (str): Directory where instance data is stored.
            identifier (str): Identifier of the instance.
            key_path (str): Path to the key pair.
        """
        credentials = AWSCredentials()
        key_id = os.path.basename(key_path)
        credentials.load(key_id)
        instance = AWSInstance(instance_dir, identifier, credentials)
        if os.path.dirname(key_path) == str(instance_dir):
            logger.debug(f"Deleting credentials: {instance.credentials.name}")
            instance.credentials.delete()
        instance.delete()

    @staticmethod
    def __create_ec2_instance(config: AWSConfig) -> str:
        """
        Create an AWS EC2 instance.

        Args:
            config (AWSConfig): Configuration for the instance.

        Returns:
            str: Identifier of the created instance.
        """
        client = boto3.resource('ec2')
        instance = client.create_instances(ImageId=config.ami,
                                            InstanceType=config.type,
                                            KeyName=config.key_name,
                                            SecurityGroupIds=config.security_groups,
                                            MinCount=1, MaxCount=1)[0]
        # Wait until the instance is running.
        instance.wait_until_running()
        return instance.instance_id

    @classmethod
    def __parse_config(cls, params: CreationPayload, credentials: AWSCredentials) -> AWSConfig:
        """
        Parse configuration parameters for creating an AWS EC2 instance.

        Args:
            params (CreationPayload): Payload containing creation parameters.
            credentials (AWSCredentials): AWS credentials object.

        Returns:
            AWSConfig: Parsed AWSConfig object.
        """
        config = {}

        # Get the specs from the yamls.
        size_specs = cls._get_size_specs()[params.size]
        os_specs = cls._get_os_specs()[params.composite_name]
        mics_specs = cls._get_misc_specs()
        arch = params.composite_name.split('-')[-1]
        # Parse the configuration.
        for spec in size_specs:
            if fnmatch.fnmatch(arch, spec):
                config['type'] = size_specs[spec]['type']
                break

        config['ami'] = os_specs['ami']
        config['zone'] = os_specs['zone']
        config['user'] = os_specs['user']
        config['key_name'] = credentials.name
        config['security_groups'] = mics_specs['security-group']

        return AWSConfig(**config)
