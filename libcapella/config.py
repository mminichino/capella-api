##
##

import logging
from typing import Union
from libcapella.config_toml import CapellaTomlConfig
from libcapella.config_data import CapellaConfigData
from libcapella.config_profile import CapellaProfileConfig

logger = logging.getLogger('libcapella.config')
logger.addHandler(logging.NullHandler())


class CapellaConfig(object):
    config = CapellaConfigData()

    def __init__(self,
                 token: Union[str, None] = None,
                 project: Union[str, None] = None,
                 email: Union[str, None] = None,
                 profile: Union[str, None] = None,
                 config_file: Union[str, None] = None,
                 config_dict: Union[dict, None] = None):
        if config_file:
            logger.debug(f"initializing with config file: {config_file}")
            self.config = CapellaTomlConfig(config_file)
        elif config_dict:
            logger.debug(f"initializing from config data")
            self.config = CapellaConfigData()
            self.config.from_dict(config_dict)
        elif profile:
            logger.debug(f"initializing with profile: {profile}")
            self.config = CapellaProfileConfig(profile=profile)
        else:
            logger.debug(f"initializing from parameters")
            self.config = CapellaConfigData()
            self.config.set_token(token)
            self.config.set_project_name(project)
            self.config.set_account_email(email)

        logger.debug(f"CapellaConfig initialized: configuration:\n{self.config}")
