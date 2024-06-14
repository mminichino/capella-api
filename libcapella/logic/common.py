##
##

import attr


def not_none(data):
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if isinstance(value, (list, dict, tuple, set)):
                data[key] = not_none(value)
            elif value is None or key is None:
                del data[key]

    elif isinstance(data, (list, set, tuple)):
        data = type(data)(not_none(item) for item in data if item is not None)

    return data


@attr.s
class Audit:
    createdBy: str = attr.ib()
    createdAt: str = attr.ib()
    modifiedBy: str = attr.ib()
    modifiedAt: str = attr.ib()
    version: int = attr.ib()
