##
##

import logging
from typing import List
from libcapella.organization import CapellaOrganization
from libcapella.logic.project import Project

logger = logging.getLogger('libcapella.project')
logger.addHandler(logging.NullHandler())


class CapellaProject(CapellaOrganization):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        org_id = self.org_id
        self.project_endpoint = f"{self.org_endpoint}/{org_id}/projects"

    @property
    def id(self):
        result = self.rest.get(self.project_endpoint).validate().as_json("data").filter("name", self.project).list_item(0)
        if not result:
            raise RuntimeError(f"Project {self.project} found")
        return Project.create(result).id

    def list_projects(self) -> List[Project]:
        result = self.rest.get(self.project_endpoint).validate().as_json("data").json_list()
        logger.debug(f"project list: found {result.size}")
        return [Project.create(r) for r in result.as_list]

    def get_project(self, project_id: str) -> Project:
        endpoint = self.project_endpoint + f"/{project_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"project get:\n{result.formatted}")
        return Project.create(result.as_dict)
