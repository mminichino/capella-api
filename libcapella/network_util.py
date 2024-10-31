##
##

import random
import ipaddress
from ipaddress import IPv4Network
from typing import Union
from libcapella.random import FastRandom


class NetworkDriver(object):

    def __init__(self):
        self.ip_space = []
        self.active_network: IPv4Network = ipaddress.ip_network("10.1.0.0/16")
        self.super_net: IPv4Network = ipaddress.ip_network("10.0.0.0/8")

    def set_active_network(self, cidr: str):
        self.active_network: IPv4Network = ipaddress.ip_network(cidr)

    def add_network(self, cidr: str) -> None:
        cidr_net = ipaddress.ip_network(cidr)
        self.ip_space.append(cidr_net)

    def get_next_subnet(self, prefix=24) -> str:
        for subnet in self.active_network.subnets(new_prefix=prefix):
            yield subnet.exploded

    def get_next_network(self) -> Union[str, None]:
        candidates = list(self.super_net.subnets(new_prefix=16))

        for network in self.ip_space:
            available = []
            for n, candidate in enumerate(candidates):
                try:
                    if network.prefixlen < 16:
                        list(network.address_exclude(candidate))
                    else:
                        list(candidate.address_exclude(network))
                except ValueError:
                    available.append(candidate)
            candidates = available

        if len(candidates) == 0:
            return None

        self.active_network = candidates[0]
        self.ip_space.append(self.active_network)
        return self.active_network.exploded

    @staticmethod
    def get_random_subnet(prefix=24):
        subnet_list = []
        subnet_list.extend(ipaddress.ip_network("10.0.0.0/8").subnets(new_prefix=prefix))
        subnet_list.extend(ipaddress.ip_network("172.16.0.0/12").subnets(new_prefix=prefix))
        subnet_list.extend(ipaddress.ip_network("192.168.0.0/16").subnets(new_prefix=prefix))
        random.shuffle(subnet_list)
        return subnet_list[FastRandom(len(subnet_list)).value - 1].exploded
