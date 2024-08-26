##
##

import attr
import attrs
from enum import Enum
from typing import Union
from libcapella.logic.common import not_none


@attr.s
class ComputeConfig:
    cpu: int = attr.ib()
    ram: int = attr.ib()


class NodeAvailability(str, Enum):
    single = 'single'
    multi = 'multi'


class SupportPlan(str, Enum):
    devpro = 'developer pro'
    enterprise = 'enterprise'


class SupportTZ(str, Enum):
    eastern_us = 'ET'
    emea = 'GMT'
    asia = 'IST'
    western_us = 'PT'


@attr.s
class Availability:
    type: NodeAvailability = attr.ib()


@attr.s
class Support:
    plan: SupportPlan = attr.ib()
    timezone: SupportTZ = attr.ib()


@attr.s
class Columnar:
    id: str = attr.ib()
    name: str = attr.ib()
    description: str = attr.ib()
    cloudProvider: str = attr.ib()
    region: str = attr.ib()
    nodes: int = attr.ib()
    currentState: str = attr.ib()
    support: Support = attr.ib()
    compute: ComputeConfig = attr.ib()
    availability: Availability = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("name"),
            data.get("description"),
            data.get("cloudProvider"),
            data.get("region"),
            data.get("nodes"),
            data.get("currentState"),
            Support(
                SupportPlan(data.get("support", {}).get("plan", "developer pro")),
                SupportTZ(data.get("support", {}).get("timezone", "PT"))
            ),
            ComputeConfig(
                data.get("compute", {}).get("cpu"),
                data.get("compute", {}).get("ram"),
            ),
            Availability(
                NodeAvailability(data.get("availability", {}).get("type", "multi"))
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


class CapellaColumnarBuilder(object):

    def __init__(self,
                 cloud,
                 name='datamart',
                 description='Columnar Cluster',
                 cpu=4,
                 ram=32,
                 quantity=1,
                 region='us-east-1',
                 availability='single',
                 plan='developer',
                 timezone='us_west'):
        self._name = name
        self._description = description
        self._cpu = cpu
        self._ram = ram
        self._quantity = quantity
        self._cloud = cloud
        self._region = region
        self._availability = availability
        self._plan = plan
        self._timezone = timezone

    def name(self, name: str):
        self._name = name
        return self

    def description(self, description: str):
        self._description = description
        return self

    def cloud(self, cloud: str):
        self._cloud = cloud
        return self

    def region(self, region: str):
        self._region = region
        return self

    def availability(self, availability: str):
        self._availability = availability
        return self

    def plan(self, plan: str):
        self._plan = plan
        return self

    def timezone(self, timezone: str):
        self._timezone = timezone
        return self

    def compute(self, machine_type: str, quantity: Union[str, int]):
        cpu, ram = machine_type.split('x')
        _cpu = int(cpu)
        _ram = int(ram)
        _quantity = int(quantity)
        self._cpu = _cpu
        self._ram = _ram
        self._quantity = _quantity
        return self

    def build(self) -> Columnar:
        if not self._availability or self._availability == "single":
            availability = "single"
        else:
            availability = "multi"

        if not self._plan or self._plan == "developer" or self._plan == "devpro" or self._plan == "developer-pro" or self._plan == "developer pro":
            plan = "developer pro"
        else:
            plan = "enterprise"

        if not self._timezone or self._timezone == "us_west" or self._timezone == "west":
            timezone = "PT"
        elif self._timezone == "us_east" or self._timezone == "east":
            timezone = "ET"
        elif self._timezone == "europe" or self._timezone == "UTC" or self._timezone.lower() == "emea":
            timezone = "GMT"
        else:
            timezone = "IST"

        return Columnar.create(dict(
            name=self._name,
            description=self._description,
            cloudProvider=self._cloud,
            region=self._region,
            nodes=self._quantity,
            support=dict(
                plan=plan,
                timezone=timezone,
            ),
            compute=dict(
                cpu=self._cpu,
                ram=self._ram,
            ),
            availability=dict(
                type=availability,
            )
        ))
