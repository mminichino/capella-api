#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.database import CapellaDatabase
from libcapella.logic.database import CapellaDatabaseBuilder

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_3')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestProject(object):
    project = "pytest-project"
    database_id = None

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_1(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, self.project)
        database = CapellaDatabase(project)

        builder = CapellaDatabaseBuilder("aws")
        builder = builder.name("pytest-cluster")
        builder = builder.description("Pytest created cluster")
        builder = builder.region("us-east-2")
        builder = builder.service_group("4x16", 3, 256)
        config = builder.build()
        result = database.create(config)
        assert result is not None
        self.database_id = result

    def test_2(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, self.project)
        database = CapellaDatabase(project, "pytest-cluster")
        database_id = database.id
        result = database.get(database_id)
        assert result.id is not None
        assert result.id == database_id
