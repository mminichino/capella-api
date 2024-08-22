#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.database import CapellaDatabase
from libcapella.logic.database import CapellaDatabaseBuilder
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
        cls.email = get_account_email()
        if not cls.email:
            raise RuntimeError('account email not set')
        config = CapellaConfig(profile="pytest")
        cls.org = CapellaOrganization(config)
        cls.project = CapellaProject(cls.org, cls.project_name, cls.email)
        if not cls.project.id:
            raise RuntimeError('project does not exist')
        cls.database = CapellaDatabase(cls.project, cls.database_name)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        if self.database.id:
            logger.debug(f"Database {self.database_name} already exists")
            return

        builder = CapellaDatabaseBuilder("aws")
        builder = builder.name(self.database_name)
        builder = builder.description("Pytest created cluster")
        builder = builder.region("us-east-2")
        builder = builder.service_group("4x16", 3, 256)
        config = builder.build()
        self.database.create(config)
        assert self.database.id is not None

    def test_2(self):
        database_id = self.database.id
        assert database_id is not None
        result = self.database.get(database_id)
        assert result.id is not None
        assert result.id == database_id

    def test_3(self):
        self.database.wait("deploying")

    def test_4(self):
        self.database.delete()

    def test_5(self):
        self.database.wait("destroying")
