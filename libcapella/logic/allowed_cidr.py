##
##

import attr
import attrs
from libcapella.logic.common import Audit, not_none


@attr.s
class AllowedCIDR:
    id: str = attr.ib()
    cidr: str = attr.ib()
    comment: str = attr.ib()
    expiresAt: str = attr.ib()
    status: str = attr.ib()
    type: str = attr.ib()
    audit: Audit = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("cidr"),
            data.get("comment"),
            data.get("expiresAt"),
            data.get("status"),
            data.get("type"),
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


class AllowedCIDRBuilder(object):

    def __init__(self,
                 cidr='0.0.0.0/0',
                 comment='Automation Created Allowed CIDR Block'):
        self._cidr = cidr
        self._comment = comment

    def cidr(self, cidr: str):
        self._cidr = cidr
        return self

    def comment(self, comment: str):
        self._comment = comment
        return self

    def build(self) -> AllowedCIDR:
        return AllowedCIDR.create(dict(
            cidr=self._cidr,
            comment=self._comment,
        ))
