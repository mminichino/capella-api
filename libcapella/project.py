##
##

import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.organization import CapellaOrganization
from libcapella.logic.project import Project
from libcapella.user import CapellaUser

logger = logging.getLogger('libcapella.project')
logger.addHandler(logging.NullHandler())


class CapellaProject(object):

    def __init__(self, org: CapellaOrganization, project: str = None, email: str = None):
        self._endpoint = f"{org.endpoint}/{org.id}/projects"
        self.rest = org.rest
        self.project_name = project if project else org.project
        self.email = email
        self.org = org
        if self.project_name:
            self.project = self.get_by_name(self.project_name, self.email)
        else:
            self.project = None

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.project:
            return None
        return self.project.id

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

    def owned_by_user(self, project_id: str, email: str) -> bool:
        user = CapellaUser(self.org, email)
        user_projects = user.projects_by_owner()
        return project_id in user_projects

    def get(self, project_id: str) -> Union[Project, None]:
        endpoint = self._endpoint + f"/{project_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return Project.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_name(self, name: str, email: str = None) -> Union[Project, None]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=50,
                                     cursor="cursor",
                                     category="pages").validate().filter("name", name).list_item(0)
        if not result:
            return None
        project = Project.create(result)
        if email and not self.owned_by_user(project.id, email):
            return None
        return project

    def create(self, project: Project):
        project_id = self.rest.post(self._endpoint, project.as_dict_striped).validate().as_json().json_key("id")
        project.id = project_id
        self.project = project
