##
##

import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.organization import CapellaOrganization
from libcapella.logic.user import User, ProjectOwnership

logger = logging.getLogger('libcapella.user')
logger.addHandler(logging.NullHandler())


class CapellaUser(object):

    def __init__(self, org: CapellaOrganization, email: Union[str, None] = None):
        self._endpoint = f"{org.endpoint}/{org.id}/users"
        self.rest = org.rest
        self.email = email
        if self.email:
            self.user_record = self.get_by_email(self.email)
        else:
            self.user_record = None

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.user_record:
            return None
        return self.user_record.id

    def list(self):
        return [User.create(r) for r in self.get_all_users()]

    def get_all_users(self) -> List[dict]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        return result.as_list

    def get(self, user_id: str) -> Union[User, None]:
        endpoint = self._endpoint + f"/{user_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return User.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_email(self, email: str) -> Union[User, None]:
        user = next((u for u in self.list() if u.email == email), None)
        while not user:
            user = next((u for u in self.list() if u.email == email), None)
        return user

    def set_project_owner(self, project_id: str):
        user_id = self.id
        endpoint = self._endpoint + f"/{user_id}"
        user_op = ProjectOwnership()
        user_op.add(project_id)
        self.rest.patch(endpoint, user_op.as_dict).validate()

    def projects_by_owner(self):
        if self.user_record:
            return [resource.id for resource in self.user_record.resources if resource.type == "project"]
        else:
            return []
