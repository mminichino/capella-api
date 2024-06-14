##
##

import attr
from libcapella.logic.common import Audit


@attr.s
class Project:
    id: str = attr.ib()
    description: str = attr.ib()
    name: str = attr.ib()
    audit: Audit = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("description"),
            data.get("name"),
            Audit(
                data.get("audit").get("createdBy"),
                data.get("audit").get("createdAt"),
                data.get("audit").get("modifiedBy"),
                data.get("audit").get("modifiedAt"),
                data.get("audit").get("version")
            )
        )
