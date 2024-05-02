##
##

import logging
from typing import List
from libcapella.base import CouchbaseCapella
from libcapella.config import CapellaConfig
from libcapella.logic.organization import Organization

logger = logging.getLogger('libcapella.organization')
logger.addHandler(logging.NullHandler())


class CapellaOrganization(CouchbaseCapella):

    def __init__(self, config: CapellaConfig):
        super().__init__(config)
        self.endpoint = "/v4/organizations"

    def list(self) -> List[Organization]:
        result = self.rest.get(self.endpoint).validate().as_json("data").json_list()
        logger.debug(f"organization list: found {result.size}")
        return [Organization.create(r) for r in result.as_list]

    def get(self, org_id: str) -> Organization:
        endpoint = self.endpoint + f"/{org_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"organization get:\n{result.formatted}")
        return Organization.create(result.as_dict)
