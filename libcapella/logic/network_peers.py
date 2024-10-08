##
##

import attr
import attrs
from typing import List
from libcapella.logic.common import Audit, not_none


@attr.s
class AzureConfig:
    azureTenantId = attr.ib()
    subscriptionId = attr.ib()
    resourceGroup = attr.ib()
    vnetId = attr.ib()
    cidr = attr.ib()

    @property
    def as_dict(self):
        # noinspection PyTypeChecker
        return attrs.asdict(self)


@attr.s
class GCPConfig:
    networkName = attr.ib()
    cidr = attr.ib()
    projectId = attr.ib()
    serviceAccount = attr.ib()

    @property
    def as_dict(self):
        # noinspection PyTypeChecker
        return attrs.asdict(self)


@attr.s
class AWSConfig:
    accountId = attr.ib()
    vpcId = attr.ib()
    region = attr.ib()
    cidr = attr.ib()

    @property
    def as_dict(self):
        # noinspection PyTypeChecker
        return attrs.asdict(self)


@attr.s
class ProviderConfig:
    providerId = attr.ib()
    AWSConfig = attr.ib(default=None)
    GCPConfig = attr.ib(default=None)
    AzureConfig = attr.ib(default=None)


@attr.s
class NetworkPeerStatus:
    state = attr.ib()
    reasoning = attr.ib()


@attr.s
class NetworkPeers:
    id: str = attr.ib()
    name: str = attr.ib()
    providerType: str = attr.ib()
    status: NetworkPeerStatus = attr.ib()
    commands: List[str] = attr.ib()
    providerConfig: ProviderConfig = attr.ib()
    audit: Audit = attr.ib()

    @classmethod
    def create(cls, data: dict, new: bool = False):
        return cls(
            data.get("id"),
            data.get("name"),
            data.get("providerType"),
            NetworkPeerStatus(
                data.get("status", {}).get("state"),
                data.get("status", {}).get("reasoning"),
            ),
            data.get("commands", []),
            ProviderConfig(
                data.get("providerConfig", {}).get("providerId"),
                AWSConfig(
                    data.get("providerConfig").get("AWSConfig").get("accountId"),
                    data.get("providerConfig").get("AWSConfig").get("vpcId"),
                    data.get("providerConfig").get("AWSConfig").get("region"),
                    data.get("providerConfig").get("AWSConfig").get("cidr"),
                ) if data.get("providerConfig", {}).get("AWSConfig") else None,
                GCPConfig(
                    data.get("providerConfig").get("GCPConfig").get("networkName"),
                    data.get("providerConfig").get("GCPConfig").get("cidr"),
                    data.get("providerConfig").get("GCPConfig").get("projectId"),
                    data.get("providerConfig").get("GCPConfig").get("serviceAccountId"),
                ) if data.get("providerConfig", {}).get("GCPConfig") else None,
                AzureConfig(
                    data.get("providerConfig").get("AzureConfig").get("azureTenantId"),
                    data.get("providerConfig").get("AzureConfig").get("subscriptionId"),
                    data.get("providerConfig").get("AzureConfig").get("resourceGroup"),
                    data.get("providerConfig").get("AzureConfig").get("vnetId"),
                    data.get("providerConfig").get("AzureConfig").get("cidr"),
                ) if data.get("providerConfig", {}).get("AzureConfig") else None,
            ) if not new else data.get("providerConfig", {}),
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
        if 'status' in result and not result['status']:
            del result['status']
        if 'commands' in result and len(result['commands']) == 0:
            del result['commands']
        return result


class NetworkPeerBuilder(object):

    def __init__(self):
        self._provider_type = "aws"
        self._name = "NetworkPeer"
        self._account_id = None
        self._vpc_id = None
        self._region = None
        self._cidr = None
        self._network_name = None
        self._project_id = None
        self._service_account = None
        self._tenant_id = None
        self._subscription_id = None
        self._resource_group = None
        self._vnet_id = None

    def provider_type(self, provider_type: str):
        self._provider_type = provider_type
        return self

    def account_id(self, account_id: str):
        self._account_id = account_id
        return self

    def vpc_id(self, vpc_id: str):
        self._vpc_id = vpc_id
        return self

    def region(self, region: str):
        self._region = region
        return self

    def cidr(self, cidr: str):
        self._cidr = cidr
        return self

    def network_name(self, network_name: str):
        self._network_name = network_name
        return self

    def project_id(self, project_id: str):
        self._project_id = project_id
        return self

    def service_account(self, service_account: str):
        self._service_account = service_account
        return self

    def tenant_id(self, tenant_id: str):
        self._tenant_id = tenant_id
        return self

    def subscription_id(self, subscription_id: str):
        self._subscription_id = subscription_id
        return self

    def resource_group(self, resource_group: str):
        self._resource_group = resource_group
        return self

    def vnet_id(self, vnet_id: str):
        self._vnet_id = vnet_id
        return self

    def build(self) -> NetworkPeers:
        provider_config = {}
        if self._provider_type == "aws":
            provider_config = AWSConfig(
                self._account_id,
                self._vpc_id,
                self._region,
                self._cidr,
            ).as_dict
        elif self._provider_type == "gcp":
            provider_config = GCPConfig(
                self._network_name,
                self._cidr,
                self._project_id,
                self._service_account,
            ).as_dict
        elif self._provider_type == "azure":
            provider_config = AzureConfig(
                self._tenant_id,
                self._subscription_id,
                self._resource_group,
                self._vnet_id,
                self._cidr,
            )
        return NetworkPeers.create(dict(
            name=self._name,
            providerType=self._provider_type,
            providerConfig=provider_config
        ), new=True)
