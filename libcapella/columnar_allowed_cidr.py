##
##

import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.logic.allowed_cidr import AllowedCIDR
from libcapella.columnar import CapellaColumnar

logger = logging.getLogger('libcapella.columnar_allowed_cidr')
logger.addHandler(logging.NullHandler())


class ColumnarAllowedCIDR(object):

    def __init__(self, columnar: CapellaColumnar, cidr: str = None):
        self._endpoint = f"{columnar.endpoint}/{columnar.id}/allowedcidrs"
        self.rest = columnar.rest
        self.cidr = cidr
        if self.cidr:
            self.allowed_cidr = self.get_by_name(self.cidr)
        else:
            self.allowed_cidr = None

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.allowed_cidr:
            return None
        return self.allowed_cidr.id

    def list(self) -> List[AllowedCIDR]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"allowed CIDR list: found {result.size}")
        return [AllowedCIDR.create(a) for a in result.as_list]

    def get(self, allowed_cidr_id: str) -> Union[AllowedCIDR, None]:
        endpoint = f"{self._endpoint}/{allowed_cidr_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return AllowedCIDR.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_name(self, cidr: str) -> Union[AllowedCIDR, None]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().filter("cidr", cidr).list_item(0)
        if not result:
            return None
        return AllowedCIDR.create(result)

    def create(self, allowed_cidr: AllowedCIDR):
        allowed_cidr_id = self.rest.post(self._endpoint, allowed_cidr.as_dict_striped).validate().as_json().json_key("id")
        allowed_cidr.id = allowed_cidr_id
        self.allowed_cidr = allowed_cidr

    def delete(self):
        if self.allowed_cidr.id:
            endpoint = f"{self._endpoint}/{self.allowed_cidr.id}"
            self.rest.delete(endpoint)
