##
##

import attr


@attr.s
class Preferences:
    sessionDuration: int = attr.ib()


@attr.s
class Audit:
    createdBy: str = attr.ib()
    createdAt: str = attr.ib()
    modifiedBy: str = attr.ib()
    modifiedAt: str = attr.ib()
    version: int = attr.ib()


@attr.s
class Organization:
    id: str = attr.ib()
    name: str = attr.ib()
    description: str = attr.ib()
    preferences: Preferences = attr.ib()
    audit: Audit = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("name"),
            data.get("description"),
            Preferences(
                data.get("preferences").get("sessionDuration")
            ),
            Audit(
                data.get("audit").get("createdBy"),
                data.get("audit").get("createdAt"),
                data.get("audit").get("modifiedBy"),
                data.get("audit").get("modifiedAt"),
                data.get("audit").get("version")
            )
        )
