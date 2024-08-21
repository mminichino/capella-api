##
##

import logging
from typing import List, Union
from libcapella.organization import CapellaOrganization
from libcapella.logic.user import User, ProjectOwnership

logger = logging.getLogger('libcapella.user')
logger.addHandler(logging.NullHandler())


class CapellaUser(object):

    def __init__(self, org: CapellaOrganization, email: Union[str, None] = None):
        self._endpoint = f"{org.endpoint}/{org.id}/users"
        self.rest = org.rest
        self.email = email

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
                  .filter("email", self.email)
                  .list_item(0))
        if not result:
            raise RuntimeError(f"User {self.email} not found")
        return User.create(result).id

    def list(self) -> List[User]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=50,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"project list: found {result.size}")
        return [User.create(r) for r in result.as_list]

    def get(self, user_id: str) -> User:
        endpoint = self._endpoint + f"/{user_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"user get:\n{result.formatted}")
        return User.create(result.as_dict)

    def get_by_email(self) -> User:
        result = (self.rest.get_paged(self._endpoint,
                                      total_tag="totalItems",
                                      pages_tag="last",
                                      per_page_tag="perPage",
                                      per_page=50,
                                      cursor="cursor",
                                      category="pages")
                  .validate()
                  .filter("email", self.email)
                  .list_item(0))
        if not result:
            raise RuntimeError(f"User {self.email} not found")
        return User.create(result)

    def set_project_owner(self, project_id: str):
        user_id = self.id
        endpoint = self._endpoint + f"/{user_id}"
        user_op = ProjectOwnership()
        user_op.add(project_id)
        self.rest.patch(endpoint, user_op.as_dict).validate()

    def projects_by_owner(self):
        user = self.get_by_email()
        return [resource.id for resource in user.resources if resource.type == "project"]
