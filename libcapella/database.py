##
##

import logging
from typing import List, Union
from libcapella.project import CapellaProject
from libcapella.logic.database import Database

logger = logging.getLogger('libcapella.database')
logger.addHandler(logging.NullHandler())


class CapellaDatabase(object):

    def __init__(self, project: CapellaProject, database: Union[str, None] = None):
        self._endpoint = f"{project.endpoint}/{project.id}/clusters"
        self.rest = project.rest
        self.project = project
        self.database = database

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.database:
            return None
        result = self.rest.get(self._endpoint).validate().as_json("data").filter("name", self.database).list_item(0)
        if not result:
            raise RuntimeError(f"Database {self.database} found")
        return Database.create(result).id

    def list(self) -> List[Database]:
        result = self.rest.get(self._endpoint).validate().as_json("data").json_list()
        logger.debug(f"database list: found {result.size}")
        return [Database.create(r) for r in result.as_list]

    def get(self, database_id: str) -> Database:
        endpoint = f"{self._endpoint}/{database_id}"
        result = self.rest.get(endpoint).validate().as_json().json_object()
        logger.debug(f"project get:\n{result.formatted}")
        return Database.create(result.as_dict)

    def create(self, database: Database):
        # import json
        # print(json.dumps(database.as_dict_striped, indent=2))
        return self.rest.post(self._endpoint, database.as_dict_striped).validate().as_json().json_key("id")
