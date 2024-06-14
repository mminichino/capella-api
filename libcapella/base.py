##
##

import logging
from libcapella.config import CapellaConfig
from restfull.restapi import RestAPI
from restfull.bearer_auth import BearerAuth

logger = logging.getLogger('libcapella.base')
logger.addHandler(logging.NullHandler())


class CouchbaseCapella(object):

    def __init__(self, config: CapellaConfig):
        self.auth_token = config.token
        self.api_host = config.api_host
        self.project = config.project
        logger.debug(f"using auth profile {config.profile} API key ID {config.key_id}")

        auth = BearerAuth(self.auth_token)
        self.rest = RestAPI(auth, self.api_host)
