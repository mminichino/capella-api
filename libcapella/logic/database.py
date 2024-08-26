##
##

import attr
import attrs
from enum import Enum
from typing import List, Union
from libcapella.logic.common import Audit, not_none

aws_storage_matrix = {
    99: 3000,
    199: 5000,
    299: 6000,
    399: 8000,
    499: 9000,
    599: 10000,
    699: 12000,
    799: 13000,
    899: 14000,
    999: 16000,
    16384: 16000
}

azure_storage_matrix = {
    64: "P6",
    128: "P10",
    256: "P15",
    512: "P20",
    1024: "P30",
    2048: "P40",
    4096: "P50",
    8192: "P60"
}


@attr.s
class CloudProvider:
    type: str = attr.ib()
    region: str = attr.ib()
    cidr: str = attr.ib()


@attr.s
class CouchbaseServer:
    version: str = attr.ib()


@attr.s
class ComputeConfig:
    cpu: int = attr.ib()
    ram: int = attr.ib()


@attr.s
class StorageConfig:
    storage: int = attr.ib()
    type: str = attr.ib()
    iops: int = attr.ib()


@attr.s
class NodeConfig:
    compute: ComputeConfig = attr.ib()
    disk: StorageConfig = attr.ib()


@attr.s
class ServiceGroup:
    node: NodeConfig = attr.ib()
    numOfNodes: int = attr.ib()
    services: List[str] = attr.ib()


class NodeAvailability(str, Enum):
    single = 'single'
    multi = 'multi'


class SupportPlan(str, Enum):
    basic = 'basic'
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
class Database:
    id: str = attr.ib()
    appServiceId: str = attr.ib()
    name: str = attr.ib()
    description: str = attr.ib()
    configurationType: str = attr.ib()
    connectionString: str = attr.ib()
    cloudProvider: CloudProvider = attr.ib()
    couchbaseServer: CouchbaseServer = attr.ib()
    serviceGroups: List[ServiceGroup] = attr.ib()
    availability: Availability = attr.ib()
    support: Support = attr.ib()
    currentState: str = attr.ib()
    audit: Audit = attr.ib()
    cmekId: str = attr.ib()

    @classmethod
    def create(cls, data: dict):
        return cls(
            data.get("id"),
            data.get("appServiceId"),
            data.get("name"),
            data.get("description"),
            data.get("configurationType"),
            data.get("connectionString"),
            CloudProvider(
                data.get("cloudProvider", {}).get("type"),
                data.get("cloudProvider", {}).get("region"),
                data.get("cloudProvider", {}).get("cidr"),
            ),
            CouchbaseServer(
                data.get("couchbaseServer", {}).get("version"),
            ),
            [
                ServiceGroup(
                    NodeConfig(
                        ComputeConfig(
                            g.get("node", {}).get("compute", {}).get("cpu"),
                            g.get("node", {}).get("compute", {}).get("ram"),
                        ),
                        StorageConfig(
                            g.get("node", {}).get("disk", {}).get("storage"),
                            g.get("node", {}).get("disk", {}).get("type"),
                            g.get("node", {}).get("disk", {}).get("iops"),
                        )
                    ),
                    g.get("numOfNodes"),
                    g.get("services"),
                ) for g in data.get("serviceGroups", [])
            ],
            Availability(
                NodeAvailability(data.get("availability", {}).get("type", "multi"))
            ),
            Support(
                SupportPlan(data.get("support", {}).get("plan", "developer pro")),
                SupportTZ(data.get("support", {}).get("timezone", "PT"))
            ),
            data.get("currentState"),
            Audit(
                data.get("audit", {}).get("createdBy"),
                data.get("audit", {}).get("createdAt"),
                data.get("audit", {}).get("modifiedBy"),
                data.get("audit", {}).get("modifiedAt"),
                data.get("audit", {}).get("version")
            ),
            data.get("cmekId"),
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


class CapellaDatabaseBuilder(object):

    def __init__(self,
                 cloud,
                 name='cbdb',
                 description='Couchbase Cluster',
                 region='us-east-1',
                 cidr='10.1.20.0/23',
                 availability='multi',
                 plan='developer',
                 timezone='us_west',
                 version=None):
        self._name = name
        self._description = description
        self._cloud = cloud
        self._region = region
        self._service_groups = []
        self._cidr = cidr
        self._availability = availability
        self._plan = plan
        self._timezone = timezone
        self._version = version

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

    def cidr(self, cidr: str):
        self._cidr = cidr
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

    def version(self, version: str):
        self._version = version
        return self

    def service_group(self, machine_type: str, quantity: Union[str, int], storage: Union[str, int], services: Union[None, str, List[str]] = None):
        cpu, ram = machine_type.split('x')
        _cpu = int(cpu)
        _ram = int(ram)

        if self._cloud == "aws":
            _storage = int(storage)
            _iops = next((aws_storage_matrix[s] for s in aws_storage_matrix if s >= _storage), None)
            _storage_type = "gp3"
        elif self._cloud == "azure":
            size, s_type = next(((s, azure_storage_matrix[s]) for s in azure_storage_matrix if s >= int(storage)), None)
            _storage = int(size)
            _storage_type = s_type
            _iops = None
        else:
            _storage = int(storage)
            _storage_type = "pd-ssd"
            _iops = None

        _quantity = int(quantity)

        if not services:
            _services = ["data", "query", "index", "search"]
        elif type(services) is str and services == "default":
            _services = ["data", "query", "index", "search"]
        else:
            _services = services

        service_group = dict(
            cpu=_cpu,
            ram=_ram,
            storage=_storage,
            iops=_iops,
            storage_type=_storage_type,
            quantity=_quantity,
            services=_services,
        )
        self._service_groups.append(service_group)

        return self

    def build(self) -> Database:
        if not self._availability or self._availability == "multi":
            availability = "multi"
        else:
            availability = "single"

        if not self._plan or self._plan == "developer" or self._plan == "devpro" or self._plan == "developer-pro" or self._plan == "developer pro":
            plan = "developer pro"
        elif self._plan == "enterprise" or self._plan == "prod" or self._plan == "production":
            plan = "enterprise"
        else:
            plan = "basic"

        if not self._timezone or self._timezone == "us_west" or self._timezone == "west":
            timezone = "PT"
        elif self._timezone == "us_east" or self._timezone == "east":
            timezone = "ET"
        elif self._timezone == "europe" or self._timezone == "UTC" or self._timezone.lower() == "emea":
            timezone = "GMT"
        else:
            timezone = "IST"

        return Database.create(dict(
            name=self._name,
            description=self._description,
            cloudProvider=dict(
                type=self._cloud,
                region=self._region,
                cidr=self._cidr,
            ),
            couchbaseServer=dict(
                version=self._version
            ),
            serviceGroups=[
                dict(
                    node=dict(
                        compute=dict(
                            cpu=g.get("cpu"),
                            ram=g.get("ram")
                        ),
                        disk=dict(
                            storage=g.get("storage"),
                            type=g.get("storage_type"),
                            iops=g.get("iops")
                        )
                    ),
                    numOfNodes=g.get("quantity"),
                    services=g.get("services")
                ) for g in self._service_groups
            ],
            availability=dict(
                type=availability,
            ),
            support=dict(
                plan=plan,
                timezone=timezone,
            )
        ))
