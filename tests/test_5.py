#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
import random
import string
from libcapella.user import CapellaUser
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.database import CapellaDatabase
from libcapella.database_allowed_cidr import CapellaAllowedCIDR
from libcapella.database_credentials import CapellaDatabaseCredentials
from libcapella.network_peers import CapellaNetworkPeers
from libcapella.app_service import CapellaAppService
from libcapella.logic.project import CapellaProjectBuilder
from libcapella.logic.database import CapellaDatabaseBuilder
from libcapella.logic.allowed_cidr import AllowedCIDRBuilder
from libcapella.logic.credentials import DatabaseCredentialsBuilder
from libcapella.logic.app_service import CapellaAppServiceBuilder
from libcapella.logic.network_peers import NetworkPeerBuilder
from tests.common import (get_account_email, gcp_authenticate, gcp_compute_default_sa, gcp_network_delete, gcp_subnet_create, gcp_region, gcp_project, gcp_network_create,
                          gcp_subnet_delete, gcp_add_peering, gcp_create_managed_zone, gcp_remove_peering, gcp_delete_managed_zone, gcp_get_network, short_hash)

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_5')
logger.addHandler(logging.NullHandler())


@pytest.mark.full_test
@pytest.mark.gcp_test
@pytest.mark.database_test
@pytest.mark.order(5)
class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_name = "pytest-cluster"
        cls.app_service_name = "pytest-app-svc"
        cls.project_name = "pytest-project"
        cls.network_name = f"pytest-{short_hash(cls.database_name)}-net"
        cls.subnet_name = f"pytest-{short_hash(cls.database_name)}-subnet"
        cls.peer_name = f"pytest-{short_hash(cls.database_name)}-peer"
        cls.managed_zone_name = f"pytest-{short_hash(cls.database_name)}-managed-zone"
        cls.network_cidr = "10.77.0.0/16"
        cls.vpc_id = None
        cls.cidr = "0.0.0.0/0"
        cls.username = "developer"
        cls.password = "P@ssw0rd!"
        cls.email = get_account_email()
        if not cls.email:
            raise RuntimeError('account email not set')
        config = CapellaConfig(profile="pytest")
        cls.org = CapellaOrganization(config)
        cls.project = CapellaProject(cls.org, cls.project_name, cls.email)
        if not cls.project.id:
            raise RuntimeError('project does not exist')
        cls.database = CapellaDatabase(cls.project, cls.database_name)
        cls.allowed_cidr = None
        cls.database_credential = None
        cls.network_peer = None
        cls.app_service = None
        gcp_authenticate()
        cls.net_link = gcp_network_create(cls.network_name)
        gcp_subnet_create(cls.subnet_name, cls.net_link, cls.network_cidr)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        if self.project.id:
            logger.debug(f"Project {self.project_name} already exists")
            return

        builder = CapellaProjectBuilder()
        builder = builder.name(self.project_name)
        config = builder.build()
        self.project.create(config)
        assert self.project.id is not None

        user = CapellaUser(self.org, self.email)
        user.set_project_owner(self.project.id)

    def test_2(self):
        if not self.database.id:
            builder = CapellaDatabaseBuilder("gcp")
            builder = builder.name(self.database_name)
            builder = builder.description("Pytest created cluster")
            builder = builder.region(gcp_region)
            builder = builder.service_group("4x16", 1, 256)
            config = builder.build()
            self.database.create(config)
            assert self.database.id is not None
            self.database.wait("deploying")

    def test_3(self):
        database_id = self.database.id
        assert database_id is not None
        result = self.database.get(database_id)
        assert result.id is not None
        assert result.id == database_id

    def test_4(self):
        self.allowed_cidr = CapellaAllowedCIDR(self.database, self.cidr)
        if not self.allowed_cidr.id:
            builder = AllowedCIDRBuilder()
            builder.cidr(self.cidr)
            config = builder.build()
            self.allowed_cidr.create(config)
            assert self.allowed_cidr.id is not None

        self.database_credential = CapellaDatabaseCredentials(self.database, self.username)
        if not self.database_credential.id:
            builder = DatabaseCredentialsBuilder(self.username, self.password)
            builder.data_read_write()
            config = builder.build()
            self.database_credential.create(config)
            assert self.database_credential.id is not None

    def test_5(self):
        service_account = gcp_compute_default_sa()
        self.network_peer = CapellaNetworkPeers(self.database)
        if not self.network_peer.id:
            gcp_project_name = gcp_project()
            builder = NetworkPeerBuilder()
            builder.provider_type("gcp")
            builder.network_name(self.network_name)
            builder.cidr(self.network_cidr)
            builder.project_id(gcp_project_name)
            builder.service_account(service_account)
            config = builder.build()
            self.network_peer.create(config)
            assert self.network_peer.id is not None
        self.network_peer.refresh()

        if not self.net_link:
            self.net_link = gcp_get_network(self.network_name).get('selfLink')
        peer_project = self.network_peer.peer_project
        peer_network = self.network_peer.peer_network
        managed_zone = self.network_peer.managed_zone
        gcp_add_peering(self.peer_name, self.network_name, peer_project, peer_network)
        gcp_create_managed_zone(self.managed_zone_name, managed_zone, self.net_link, True, peer_project, peer_network, service_account)
        self.database.wait("peering")

    def test_6(self):
        self.app_service = CapellaAppService(self.database)
        if not self.app_service.id:
            builder = CapellaAppServiceBuilder()
            builder.name(self.app_service_name)
            builder.compute("4x8", 1)
            config = builder.build()
            self.app_service.create(config)
            assert self.app_service.id is not None
            self.app_service.wait("healthy", until=True)

        self.app_service.delete()
        self.app_service.wait("destroying")

    def test_7(self):
        self.database.delete()
        self.database.wait("destroying")
        gcp_remove_peering(self.peer_name, self.network_name)
        gcp_delete_managed_zone(self.managed_zone_name)
        gcp_subnet_delete(self.subnet_name)
        gcp_network_delete(self.network_name)
