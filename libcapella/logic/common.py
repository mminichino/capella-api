##
##

import attr


@attr.s
class Audit:
    createdBy: str = attr.ib()
    createdAt: str = attr.ib()
    modifiedBy: str = attr.ib()
    modifiedAt: str = attr.ib()
    version: int = attr.ib()
