##
##

import attr
import attrs
from libcapella.logic.common import Audit, not_none


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
                data.get("audit", {}).get("createdBy"),
                data.get("audit", {}).get("createdAt"),
                data.get("audit", {}).get("modifiedBy"),
                data.get("audit", {}).get("modifiedAt"),
                data.get("audit", {}).get("version")
            )
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
        return result


class CapellaProjectBuilder(object):

    def __init__(self,
                 name='default',
                 description='Capella Project'):
        self._name = name
        self._description = description

    def name(self, name: str):
        self._name = name
        return self

    def description(self, description: str):
        self._description = description
        return self

    def build(self) -> Project:
        return Project.create(dict(
            name=self._name,
            description=self._description
        ))
