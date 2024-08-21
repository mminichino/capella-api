##
##

import logging
from typing import List, Union
from libcapella.organization import CapellaOrganization
from libcapella.logic.project import Project
from libcapella.user import CapellaUser

logger = logging.getLogger('libcapella.project')
logger.addHandler(logging.NullHandler())


class CapellaProject(object):

    def __init__(self, org: CapellaOrganization, project: Union[str, None] = None):
        self._endpoint = f"{org.endpoint}/{org.id}/projects"
        self.rest = org.rest
        self.project = project if project else org.project
        self.org = org

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        result = (self.rest.get_paged(self._endpoint,
                                      total_tag="totalItems",
                                      pages_tag="last",
                                      per_page_tag="perPage",
                                      per_page=50,
                                      cursor="cursor",
                                      category="pages")
                  .validate()
                  .filter("name", self.project)
                  .list_item(0))
        if not result:
            raise RuntimeError(f"Project {self.project} not found")
        return Project.create(result).id

    def list(self) -> List[Project]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=50,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"project list: found {result.size}")
        return [Project.create(r) for r in result.as_list]

    def list_by_user(self, email: str) -> List[Project]:
        user = CapellaUser(self.org, email)
        user_projects = user.projects_by_owner()
        projects = self.list()
        return [p for p in projects if p.id in user_projects]

    def get(self, project_id: str) -> Project:
        endpoint = self._endpoint + f"/{project_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"project get:\n{result.formatted}")
        return Project.create(result.as_dict)

    def create(self, project: Project):
        return self.rest.post(self._endpoint, project.as_dict_striped).validate().as_json().json_key("id")
