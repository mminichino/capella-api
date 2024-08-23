##
##

import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.logic.credentials import DatabaseCredentials
from libcapella.database import CapellaDatabase

logger = logging.getLogger('libcapella.database_credentials')
logger.addHandler(logging.NullHandler())


class CapellaDatabaseCredentials(object):

    def __init__(self, database: CapellaDatabase, username: str = None):
        self._endpoint = f"{database.endpoint}/{database.id}/users"
        self.rest = database.rest
        self.username = username
        if self.username:
            self.db_credentials = self.get_by_name(self.username)
        else:
            self.db_credentials = None

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.db_credentials:
            return None
        return self.db_credentials.id

    def list(self) -> List[DatabaseCredentials]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"database credentials list: found {result.size}")
        return [DatabaseCredentials.create(a) for a in result.as_list]

    def get(self, db_user_id: str) -> Union[DatabaseCredentials, None]:
        endpoint = f"{self._endpoint}/{db_user_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return DatabaseCredentials.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_name(self, username: str) -> Union[DatabaseCredentials, None]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().filter("name", username).list_item(0)
        if not result:
            return None
        return DatabaseCredentials.create(result)

    def create(self, db_user: DatabaseCredentials):
        db_user_id = self.rest.post(self._endpoint, db_user.as_dict_striped).validate().as_json().json_key("id")
        db_user.id = db_user_id
        self.db_credentials = db_user

    def delete(self):
        if self.db_credentials.id:
            endpoint = f"{self._endpoint}/{self.db_credentials.id}"
            self.rest.delete(endpoint)
