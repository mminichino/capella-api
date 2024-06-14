##
##

import logging
from typing import List, Union
from libcapella.organization import CapellaOrganization
from libcapella.logic.project import Project

logger = logging.getLogger('libcapella.project')
logger.addHandler(logging.NullHandler())


class CapellaProject(object):

    def __init__(self, org: CapellaOrganization, project: Union[str, None] = None):
        self.endpoint = f"{org.endpoint}/{org.id}/projects"
        self.rest = org.rest
        self.project = project if project else org.project

    @property
    def id(self):
        result = self.rest.get(self.endpoint).validate().as_json("data").filter("name", self.project).list_item(0)
        if not result:
            raise RuntimeError(f"Project {self.project} found")
        return Project.create(result).id

    def list(self) -> List[Project]:
        result = self.rest.get(self.endpoint).validate().as_json("data").json_list()
        logger.debug(f"project list: found {result.size}")
        return [Project.create(r) for r in result.as_list]

    def get(self, project_id: str) -> Project:
        endpoint = self.endpoint + f"/{project_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"project get:\n{result.formatted}")
        return Project.create(result.as_dict)
