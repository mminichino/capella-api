##
##

import attr
import attrs
from typing import Union
from libcapella.logic.common import Audit, not_none


@attr.s
class ComputeConfig:
    cpu: int = attr.ib()
    ram: int = attr.ib()


@attr.s
class AppService:
    id: str = attr.ib()
    name: str = attr.ib()
    description: str = attr.ib()
    cloudProvider: str = attr.ib()
    nodes: int = attr.ib()
    compute: ComputeConfig = attr.ib()
    clusterId: str = attr.ib()
    currentState: str = attr.ib()
    version: str = attr.ib()
    audit: Audit = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("name"),
            data.get("description"),
            data.get("cloudProvider"),
            data.get("nodes"),
            ComputeConfig(
                data.get("compute", {}).get("cpu"),
                data.get("compute", {}).get("ram"),
            ),
            data.get("clusterId"),
            data.get("currentState"),
            data.get("version"),
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


class CapellaAppServiceBuilder(object):

    def __init__(self):
        self._name = "AppService"
        self._description = "Automation Generated App Service"
        self._version = None
        self._nodes = 2
        self._cpu = 8
        self._ram = 16

    def name(self, name: str):
        self._name = name
        return self

    def description(self, description: str):
        self._description = description
        return self

    def version(self, version: str):
        self._version = version
        return self

    def compute(self, machine_type: str, nodes: Union[str, int]):
        cpu, ram = machine_type.split('x')
        _cpu = int(cpu)
        _ram = int(ram)
        _nodes = int(nodes)
        self._cpu = _cpu
        self._ram = _ram
        self._nodes = _nodes
        return self

    def build(self) -> AppService:
        return AppService.create(dict(
            name=self._name,
            description=self._description,
            nodes=self._nodes,
            compute=dict(
                cpu=self._cpu,
                ram=self._ram,
            ),
            version=self._version
        ))
