##
##

import re
import logging
from typing import List, Union
from restfull.restapi import NotFoundError
from libcapella.logic.network_peers import NetworkPeers
from libcapella.database import CapellaDatabase

logger = logging.getLogger('libcapella.network_peers')
logger.addHandler(logging.NullHandler())


class CapellaNetworkPeers(object):

    def __init__(self, database: CapellaDatabase, name: str = "NetworkPeer"):
        self._endpoint = f"{database.endpoint}/{database.id}/networkPeers"
        self.rest = database.rest
        self.name = name
        self.network_peer = self.get_by_name(self.name)

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def id(self):
        if not self.network_peer:
            return None
        return self.network_peer.id

    @property
    def this(self) -> NetworkPeers:
        return self.network_peer

    @property
    def provider_id(self):
        return self.network_peer.providerConfig.providerId

    @property
    def hosted_zone_id(self):
        cmd_list = self.network_peer.commands if self.network_peer.commands else []
        return next((re.search('--hosted-zone-id=(.+?) ', z).group(1) for z in cmd_list if re.search('--hosted-zone-id', z)), None)

    @property
    def peer_project(self):
        cmd_list = self.network_peer.commands if self.network_peer.commands else []
        return next((re.search('--peer-project\s+(.+?) ', z).group(1) for z in cmd_list if re.search('--peer-project', z)), None)

    @property
    def peer_network(self):
        cmd_list = self.network_peer.commands if self.network_peer.commands else []
        return next((re.search('--peer-network\s+(.+?)$', z).group(1) for z in cmd_list if re.search('--peer-network', z)), None)

    @property
    def managed_zone(self):
        cmd_list = self.network_peer.commands if self.network_peer.commands else []
        return next((re.search('--dns-name=(.+?) ', z).group(1) for z in cmd_list if re.search('--dns-name', z)), None)

    def refresh(self):
        self.network_peer = self.get(self.network_peer.id)

    def list(self) -> List[NetworkPeers]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().json_list()
        logger.debug(f"network peer list: found {result.size}")
        return [NetworkPeers.create(a) for a in result.as_list]

    def get(self, peer_id: str) -> Union[NetworkPeers, None]:
        endpoint = f"{self._endpoint}/{peer_id}"
        try:
            result = self.rest.get(endpoint).validate().as_json().json_object()
            return NetworkPeers.create(result.as_dict)
        except NotFoundError:
            return None

    def get_by_name(self, name: str) -> Union[NetworkPeers, None]:
        result = self.rest.get_paged(self._endpoint,
                                     total_tag="totalItems",
                                     pages_tag="last",
                                     per_page_tag="perPage",
                                     per_page=100,
                                     cursor="cursor",
                                     category="pages").validate().filter("name", name).list_item(0)
        if not result:
            return None
        return NetworkPeers.create(result)

    def create(self, network_peer: NetworkPeers):
        network_peer_id = self.rest.post(self._endpoint, network_peer.as_dict_striped).validate().as_json().json_key("id")
        network_peer.id = network_peer_id
        self.network_peer = network_peer

    def delete(self):
        if self.network_peer.id:
            endpoint = f"{self._endpoint}/{self.network_peer.id}"
            self.rest.delete(endpoint)
