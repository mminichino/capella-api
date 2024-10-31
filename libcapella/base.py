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
        self.config = config.config
        self.auth_token = self.config.token
        self.api_host = self.config.api_host

        auth = BearerAuth(self.auth_token)
        self.rest = RestAPI(auth, self.api_host)
        self.rest.retry_server_errors()
