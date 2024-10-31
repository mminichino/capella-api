#!/usr/bin/env python3

import os
import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.logic.database import CapellaDatabaseBuilder
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.database import CapellaDatabase
from libcapella.database_allowed_cidr import CapellaAllowedCIDR
from libcapella.database_credentials import CapellaDatabaseCredentials
from libcapella.logic.allowed_cidr import AllowedCIDRBuilder
from libcapella.logic.credentials import DatabaseCredentialsBuilder
from tests.common import aws_region

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_9')
logger.addHandler(logging.NullHandler())


@pytest.mark.full_test
@pytest.mark.toml_test
@pytest.mark.order(9)
class TestTomlConfigId(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = os.path.join(current_dir, "test_file_2.toml")
        config = CapellaConfig(config_file=config_file)
        org = CapellaOrganization(config)
        cls.project = CapellaProject(org)
        if not cls.project.id:
            raise RuntimeError('project does not exist')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        database = CapellaDatabase(self.project)
        if not database.id:
            builder = CapellaDatabaseBuilder("aws")
            builder = builder.description("Pytest created cluster")
            builder = builder.region(aws_region)
            builder = builder.service_group("4x16", 1, 256)
            config = builder.build()
            database.create(config)
            assert database.id is not None
            database.wait("deploying")

        cidr = "0.0.0.0/0"
        allowed_cidr = CapellaAllowedCIDR(database, cidr)
        if not allowed_cidr.id:
            builder = AllowedCIDRBuilder()
            builder.cidr(cidr)
            config = builder.build()
            allowed_cidr.create(config)
            assert allowed_cidr.id is not None

        username = "developer"
        password = "P@ssw0rd!"
        database_credential = CapellaDatabaseCredentials(database, username)
        if not database_credential.id:
            builder = DatabaseCredentialsBuilder(username, password)
            builder.data_read_write()
            config = builder.build()
            database_credential.create(config)
            assert database_credential.id is not None

    def test_2(self):
        database = CapellaDatabase(self.project)
        assert database.id is not None

    def test_3(self):
        database = CapellaDatabase(self.project)
        database.delete()
        database.wait("destroying")
