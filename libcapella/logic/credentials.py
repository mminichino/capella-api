##
##

import attr
import attrs
from typing import List
from libcapella.logic.common import Audit, not_none


@attr.s
class ResourceScope:
    name: str = attr.ib()
    collections: List[str] = attr.ib()


@attr.s
class BucketAccessSpec:
    name: str = attr.ib()
    scopes: List[ResourceScope] = attr.ib()


@attr.s
class ResourceBucket:
    buckets: List[BucketAccessSpec] = attr.ib()


@attr.s
class Access:
    privileges: List[str] = attr.ib()
    resources: ResourceBucket = attr.ib(default={})


@attr.s
class DatabaseCredentials:
    id: str = attr.ib()
    name: str = attr.ib()
    password: str = attr.ib()
    audit: Audit = attr.ib()
    access: List[Access] = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("name"),
            data.get("password"),
            Audit(
                data.get("audit", {}).get("createdBy"),
                data.get("audit", {}).get("createdAt"),
                data.get("audit", {}).get("modifiedBy"),
                data.get("audit", {}).get("modifiedAt"),
                data.get("audit", {}).get("version")
            ),
            [
                Access(
                    a.get("privileges", []),
                    ResourceBucket(
                        [
                            BucketAccessSpec(
                                b.get("name"),
                                [
                                    ResourceScope(
                                        s.get("name"),
                                        s.get("collections", []),
                                    ) for s in b.get("scopes", [])
                                ]
                            ) for b in a.get("resources", {}).get("buckets", [])
                        ]
                    )
                ) for a in data.get("access", [])
            ]
        )

    @property
    def as_dict(self):
        # noinspection PyTypeChecker
        return attrs.asdict(self)

    @property
    def as_dict_striped(self):
        result = not_none(self.as_dict)
        if 'audit' in result:
            del result['audit']
        if len(result.get('access')[0].get('resources', {}).get('buckets', [])) == 0:
            del result['access'][0]['resources']
        return result


class DatabaseCredentialsBuilder(object):

    def __init__(self,
                 username='developer',
                 password='P@ssw0rd!',
                 ):
        self._username = username
        self._password = password
        self._privileges = []

    def username(self, username: str):
        self._username = username
        return self

    def password(self, password: str):
        self._password = password
        return self

    def data_reader(self):
        self._privileges.append("data_reader")

    def data_writer(self):
        self._privileges.append("data_writer")

    def data_read_write(self):
        self._privileges.extend(["data_reader", "data_writer"])

    def build(self) -> DatabaseCredentials:
        return DatabaseCredentials.create(dict(
            name=self._username,
            password=self._password,
            access=[
                dict(
                    privileges=self._privileges,
                )
            ]
        ))
