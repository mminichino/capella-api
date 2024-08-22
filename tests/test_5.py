#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.columnar import CapellaColumnar
from libcapella.logic.columnar import CapellaColumnarBuilder
from tests.common import get_account_email

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_4')
logger.addHandler(logging.NullHandler())


@pytest.mark.columnar_test
@pytest.mark.order(5)
class TestColumnar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls. cluster_name = "pytest-columnar"
        cls.project_name = "pytest-project"
        cls.email = get_account_email()
        if not cls.email:
            raise RuntimeError('account email not set')
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, cls.project_name, cls.email)
        if not project.id:
            raise RuntimeError('project does not exist')
        cls.cluster = CapellaColumnar(project)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        if self.cluster.id:
            logger.debug(f"Cluster {self.cluster_name} already exists")
            return

        builder = CapellaColumnarBuilder("aws")
        builder = builder.name(self.cluster_name)
        builder = builder.description("Pytest created cluster")
        builder = builder.region("us-east-1")
        builder = builder.compute("4x32", 4)
        config = builder.build()
        self.cluster.create(config)
        assert self.cluster.id is not None

    def test_2(self):
        columnar_id = self.cluster.id
        assert columnar_id is not None
        result = self.cluster.get(columnar_id)
        assert result.id is not None
        assert result.id == columnar_id

    def test_3(self):
        self.cluster.wait("deploying")

    def test_4(self):
        self.cluster.delete()

    def test_5(self):
        self.cluster.wait("destroying")
