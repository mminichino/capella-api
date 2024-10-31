##
##

import logging
import os
import configparser
from configparser import SectionProxy
from pathlib import Path
from libcapella.config_data import CapellaConfigData

logger = logging.getLogger('libcapella.config_profile')
logger.addHandler(logging.NullHandler())


class CapellaProfileConfig(CapellaConfigData):

    def __init__(self, filename: str = None, profile: str = 'default'):
        super().__init__()
        self.home_dir = Path.home()
        self.config_directory = os.path.join(self.home_dir, '.capella')
        self.config_file = os.path.join(self.config_directory, 'credentials')
        self.profile = profile
        logger.debug(f"using profile: {self.profile}")
        self.filename = filename if filename else self.config_file
        self._token_file = None
        self._token_file_path = os.path.join(self.config_directory, 'default-api-key-token.txt')

        self.read_config_file()
        self.read_token_file()

    def read_config_file(self):
        config_data = configparser.ConfigParser()
        try:
            config_data.read(self.filename)
            default_config = config_data['default']
            self.read_config(default_config)
            if self.profile != 'default':
                profile_config = config_data[self.profile]
                self.read_config(profile_config)
        except KeyError:
            raise RuntimeError(f"profile {self.profile} does not exist in config file {self.config_file}")
        except Exception as err:
            raise RuntimeError(f"can not read config file {self.config_file}: {err}")

    def read_config(self, profile_config: SectionProxy):
        if profile_config.get('api_host'):
            self._api_host = profile_config.get('api_host')
        if profile_config.get('token_file'):
            self._token_file = profile_config.get('token_file')
            self._token_file_path = os.path.join(self.config_directory, self._token_file)
        if profile_config.get('organization'):
            self._organization_name = profile_config.get('organization')
        if profile_config.get('project'):
            self._project_name = profile_config.get('project')
        if profile_config.get('account_email'):
            self._account_email = profile_config.get('account_email')

    def read_token_file(self):
        if os.path.exists(self._token_file_path):
            try:
                credential_data = dict(line.split(':', 1) for line in open(self._token_file_path))
                self._token = credential_data.get('APIKeyToken').strip()
            except AttributeError:
                raise RuntimeError(f"token file {self._token_file} does not contain an API key and token")
            except Exception as err:
                raise RuntimeError(f"can not read credential file {self._token_file}: {err}")
        else:
            raise RuntimeError("Please create Capella token file (i.e. $HOME/.capella/default-api-key-token.txt)")
