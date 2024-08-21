##

import os
import logging
import warnings
import configparser
from pathlib import Path

warnings.filterwarnings("ignore")
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
logger = logging.getLogger('tests.common')
logger.addHandler(logging.NullHandler())
logging.getLogger("docker").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

local_config_file = os.path.join(Path.home(), '.capella', 'credentials')


def get_account_email():
    if os.environ.get('CAPELLA_USER_EMAIL'):
        return os.environ.get('CAPELLA_USER_EMAIL')
    elif os.path.exists(local_config_file):
        config_data = configparser.ConfigParser()
        config_data.read(local_config_file)
        if 'default' in config_data:
            pytest_config = config_data['default']
            if pytest_config.get('account_email'):
                return pytest_config.get('account_email')
    else:
        return None
