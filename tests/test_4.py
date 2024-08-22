#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.database import CapellaDatabase
from libcapella.allowed_cidr import CapellaAllowedCIDR
from libcapella.credentials import CapellaDatabaseCredentials
from libcapella.logic.database import CapellaDatabaseBuilder
from libcapella.logic.allowed_cidr import AllowedCIDRBuilder
from libcapella.logic.credentials import DatabaseCredentialsBuilder
from tests.common import get_account_email

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_3')
logger.addHandler(logging.NullHandler())


@pytest.mark.database_test
@pytest.mark.order(4)
class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database_name = "pytest-cluster"
        cls.project_name = "pytest-project"
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

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        if not self.database.id:
            builder = CapellaDatabaseBuilder("aws")
            builder = builder.name(self.database_name)
            builder = builder.description("Pytest created cluster")
            builder = builder.region("us-east-2")
            builder = builder.service_group("4x16", 3, 256)
            config = builder.build()
            self.database.create(config)
            assert self.database.id is not None

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

    def test_2(self):
        database_id = self.database.id
        assert database_id is not None
        result = self.database.get(database_id)
        assert result.id is not None
        assert result.id == database_id

    def test_3(self):
        self.database.wait("deploying")

    # def test_4(self):
    #     self.database.delete()
    #
    # def test_5(self):
    #     self.database.wait("destroying")
