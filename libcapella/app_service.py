##
##

import time
import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.logic.app_service import AppService
from libcapella.database import CapellaDatabase

logger = logging.getLogger('libcapella.app_service')
logger.addHandler(logging.NullHandler())


class CapellaAppService(object):

    def __init__(self, database: CapellaDatabase):
        self._endpoint = f"{database.endpoint}/{database.id}/appservices"
        self._list_endpoint = f"{database.project.org.id_endpoint}/appservices"
        self.database = database
        self.rest = database.rest
        self.app_service = self.get_by_db(database.id)

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.app_service:
            return None
        return self.app_service.id

    def list(self) -> List[AppService]:
        result = self.rest.get_paged(self._list_endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"app service list: found {result.size}")
        return [AppService.create(a) for a in result.as_list]

    def get(self, app_service_id: str) -> Union[AppService, None]:
        if not app_service_id:
            return None
        endpoint = f"{self._endpoint}/{app_service_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return AppService.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_db(self, database_id: str) -> Union[AppService, None]:
        if not database_id:
            return None
        result = self.rest.get_paged(self._list_endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().filter("clusterId", database_id).list_item(0)
        if not result:
            return None
        return AppService.create(result)

    def create(self, app_service: AppService):
        app_service_id = self.rest.post(self._endpoint, app_service.as_dict_striped).validate().as_json().json_key("id")
        app_service.id = app_service_id
        self.app_service = app_service

    def wait(self, state, until: bool = False, retry_count: int = 240):
        if not self.app_service:
            return True
        for retry_number in range(retry_count + 1):
            check = self.get(self.app_service.id)
            if not until and check and check.currentState != state:
                time.sleep(1)
                return True
            elif until and check and check.currentState == state:
                time.sleep(1)
                return True
            elif not check:
                return True
            else:
                if retry_number == retry_count:
                    return False
                logger.debug(f"Waiting for app service {self.app_service.name} to reach state {state}")
                time.sleep(5)

    def delete(self):
        if self.app_service.id:
            endpoint = f"{self._endpoint}/{self.app_service.id}"
            self.rest.delete(endpoint)
