##
##

import attr
import attrs
from typing import Optional, List
from libcapella.logic.common import Audit


@attr.s
class Resources:
    type: str = attr.ib()
    id: str = attr.ib()
    roles: List[str] = attr.ib()


@attr.s
class User:
    id: str = attr.ib()
    name: str = attr.ib()
    email: str = attr.ib()
    status: str = attr.ib()
    inactive: bool = attr.ib()
    organizationId: str = attr.ib()
    organizationRoles: List[str] = attr.ib()
    lastLogin: str = attr.ib()
    region: str = attr.ib()
    timeZone: str = attr.ib()
    enableNotifications: bool = attr.ib()
    expiresAt: str = attr.ib()
    resources: List[Resources] = attr.ib()
    audit: Audit = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get('id'),
            data.get('name'),
            data.get('email'),
            data.get('status'),
            data.get('inactive'),
            data.get('organizationId'),
            data.get('organizationRoles', []),
            data.get('lastLogin'),
            data.get('region'),
            data.get('timeZone'),
            data.get('enableNotifications'),
            data.get('expiresAt'),
            [
                Resources(
                    r.get('type'),
                    r.get('id'),
                    r.get('roles', [])
                ) for r in data.get('resources', [])
            ],
            Audit(
                data.get("audit", {}).get("createdBy"),
                data.get("audit", {}).get("createdAt"),
                data.get("audit", {}).get("modifiedBy"),
                data.get("audit", {}).get("modifiedAt"),
                data.get("audit", {}).get("version")
            )
        )


@attr.s
class UserOpValue:
    id: Optional[str] = attr.ib(default=None)
    type: Optional[str] = attr.ib(default=None)
    roles: Optional[List[str]] = attr.ib(default=None)


@attr.s
class UserOp:
    op: Optional[str] = attr.ib(default=None)
    path: Optional[str] = attr.ib(default=None)
    value: Optional[UserOpValue] = attr.ib(default=None)


@attr.s
class ProjectOwnership:
    user_op_list: Optional[List[UserOp]] = attr.ib(default=[])

    def add(self, project_id: str):
        opo = UserOp()
        opo.op = "add"
        opo.path = f"/resources/{project_id}"
        opo.value = UserOpValue(id=project_id, type="project", roles=["projectOwner"])
        self.user_op_list.append(opo)

    @property
    def as_dict(self):
        return list(attrs.asdict(o) for o in self.__dict__["user_op_list"])
