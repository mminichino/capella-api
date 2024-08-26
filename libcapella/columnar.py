##
##

import time
import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.project import CapellaProject
from libcapella.logic.columnar import Columnar

logger = logging.getLogger('libcapella.columnar')
logger.addHandler(logging.NullHandler())


class CapellaColumnar(object):

    def __init__(self, project: CapellaProject, cluster: Union[str, None] = None):
        self._endpoint = f"{project.endpoint}/{project.id}/analyticsClusters"
        self.rest = project.rest
        self.project = project
        self.cluster_name = cluster
        if self.cluster_name:
            self.cluster = self.get_by_name(self.cluster_name)
        else:
            self.cluster = None

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.cluster:
            return None
        return self.cluster.id

    @property
    def this(self) -> Columnar:
        return self.cluster

    def refresh(self):
        self.cluster = self.get(self.cluster.id)

    def list(self) -> List[Columnar]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=50,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"database list: found {result.size}")
        return [Columnar.create(r) for r in result.as_list]

    def get(self, columnar_id: str) -> Union[Columnar, None]:
        if not columnar_id:
            return None
        endpoint = f"{self._endpoint}/{columnar_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return Columnar.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_name(self, name: str) -> Union[Columnar, None]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=50,
                                     cursor="cursor",
                                     category="pages").validate().filter("name", name).list_item(0)
        if not result:
            return None
        return Columnar.create(result)

    def create(self, columnar: Columnar):
        cluster_id = self.rest.post(self._endpoint, columnar.as_dict_striped).validate().as_json().json_key("id")
        columnar.id = cluster_id
        self.cluster = columnar

    def wait(self, state, retry_count: int = 240):
        if not self.cluster:
            return True
        for retry_number in range(retry_count + 1):
            check = self.get(self.cluster.id)
            if check and check.currentState != state:
                time.sleep(1)
                return True
            elif not check:
                return True
            else:
                if retry_number == retry_count:
                    return False
                logger.debug(f"Waiting for cluster {self.cluster.name} to reach state {state}")
                time.sleep(5)

    def delete(self):
        if self.cluster.id:
            endpoint = f"{self._endpoint}/{self.cluster.id}"
            self.rest.delete(endpoint)
