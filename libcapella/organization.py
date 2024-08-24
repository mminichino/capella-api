##
##

import logging
from typing import List
from libcapella.base import CouchbaseCapella
from libcapella.logic.organization import Organization

logger = logging.getLogger('libcapella.organization')
logger.addHandler(logging.NullHandler())


class CapellaOrganization(CouchbaseCapella):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._endpoint = "/v4/organizations"
        self.organization = self.get_default()

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id_endpoint(self):
        return f"{self.endpoint}/{self.id}"

    @property
    def id(self):
        if not self.organization:
            return None
        return self.organization.id

    def list(self) -> List[Organization]:
        result = self.rest.get(self._endpoint).validate().as_json("data").json_list()
        logger.debug(f"organization list: found {result.size}")
        return [Organization.create(r) for r in result.as_list]

    def get(self, org_id: str) -> Organization:
        endpoint = self._endpoint + f"/{org_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"organization get:\n{result.formatted}")
        return Organization.create(result.as_dict)

    def get_default(self) -> Organization:
        result = self.list()
        if not len(result) >= 1:
            raise RuntimeError("No organizations found")
        return result[0]
