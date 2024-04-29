import yaml

from pathlib import Path
from utils.log import logger_manager
from utils.singleton import singleton
from utils.root_path import DEFAULT_CONFIG_PATH

logger = logger_manager.logger


@singleton
class ResourcePool:
    """
    The class of resource pool, to deserialize and load the resource
    """

    def __init__(self, resource_file_name):
        self.resource_file_name = resource_file_name
        self.resource_file_base_path = DEFAULT_CONFIG_PATH
        self.GROUPS = None
        self.ADMIN = None
        self.resource = self.load()

    def load(self):
        # Load environment specific config file
        resource_file_path = self.resource_file_base_path / self.resource_file_name

        if Path(resource_file_path).is_file():
            logger.info(
                f"Local config found {resource_file_path}",
            )
            yconfig = self.load_resource_from_yaml(resource_file_path)
            self.GROUPS = yconfig["groups"]["enable"]
            self.ADMIN = yconfig["administrators"]["wxid"]
            return yconfig
        else:
            logger.info(
                f"Local config not found {resource_file_path}",
            )
            assert False

    @staticmethod
    def load_resource_from_yaml(file_path):
        logger.info(f"Load resource, file name is {file_path}")
        with open(file_path, "r", encoding="utf-8") as my_resource:
            temp_resource = yaml.safe_load(my_resource)
        return temp_resource

    @staticmethod
    def write_resource_to_yaml(data, file_path):
        logger.info(f"Write resource, file name is {file_path}")
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.dump(data, file)

    def rewrite_reload(self):
        resource_file_path = self.resource_file_base_path / self.resource_file_name
        self.write_resource_to_yaml(self.resource, resource_file_path)
        self.resource = self.load()
