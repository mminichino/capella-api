#!/usr/bin/env python3

import logging
import time
import pytest
import warnings
import unittest
from libcapella.user import CapellaUser
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.database import CapellaDatabase
from libcapella.database_allowed_cidr import CapellaAllowedCIDR
from libcapella.database_credentials import CapellaDatabaseCredentials
from libcapella.app_service import CapellaAppService
from libcapella.logic.project import CapellaProjectBuilder
from libcapella.logic.database import CapellaDatabaseBuilder
from libcapella.logic.allowed_cidr import AllowedCIDRBuilder
from libcapella.logic.credentials import DatabaseCredentialsBuilder
from libcapella.logic.app_service import CapellaAppServiceBuilder
from tests.common import (short_hash, get_account_email, azure_region)

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_6')
logger.addHandler(logging.NullHandler())


@pytest.mark.full_test
@pytest.mark.azure_test
@pytest.mark.database_test
@pytest.mark.order(6)
class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_name = "pytest-cluster"
        cls.app_service_name = "pytest-app-svc"
        cls.project_name = "pytest-project"
        cls.network_name = f"pytest-{short_hash(cls.database_name)}-net"
        cls.rg_name = "pytest-rg"
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
            builder = CapellaDatabaseBuilder("azure")
            builder = builder.name(self.database_name)
            builder = builder.description("Pytest created cluster")
            builder = builder.region(azure_region)
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

    def test_6(self):
        self.database.delete()
        self.database.wait("destroying")

    def test_7(self):
        if not self.database.id:
            builder = CapellaDatabaseBuilder("azure")
            builder = builder.name(self.database_name)
            builder = builder.description("Pytest created cluster")
            builder = builder.region(azure_region)
            builder = builder.service_group("4x16", 3, 256, ultra=True)
            config = builder.build()
            self.database.create(config)
            assert self.database.id is not None
            self.database.wait("deploying")

        time.sleep(5)
        self.database.delete()
        self.database.wait("destroying")
