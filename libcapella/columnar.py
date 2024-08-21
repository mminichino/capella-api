##
##

import logging
from typing import List, Union
from libcapella.project import CapellaProject
from libcapella.logic.columnar import Columnar

logger = logging.getLogger('libcapella.columnar')
logger.addHandler(logging.NullHandler())


class CapellaColumnar(object):

    def __init__(self, project: CapellaProject, cluster: Union[str, None] = None):
        self._endpoint = f"{project.endpoint}/{project.id}/analyticsClusters"
        self.rest = project.rest
        self.project = project
        self.cluster = cluster

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.cluster:
            return None
        result = self.rest.get(self._endpoint).validate().as_json("data").filter("name", self.cluster).list_item(0)
        if not result:
            raise RuntimeError(f"Columnar cluster {self.cluster} not found")
        return Columnar.create(result).id

    def list(self) -> List[Columnar]:
        result = self.rest.get(self._endpoint).validate().as_json("data").json_list()
        logger.debug(f"database list: found {result.size}")
        return [Columnar.create(r) for r in result.as_list]

    def get(self, columnar_id: str) -> Columnar:
        endpoint = f"{self._endpoint}/{columnar_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"project get:\n{result.formatted}")
        return Columnar.create(result.as_dict)

    def create(self, columnar: Columnar):
        return self.rest.post(self._endpoint, columnar.as_dict_striped).validate().as_json().json_key("id")
