#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.columnar import CapellaColumnar
from libcapella.columnar_allowed_cidr import ColumnarAllowedCIDR
from libcapella.logic.columnar import CapellaColumnarBuilder
from libcapella.logic.allowed_cidr import AllowedCIDRBuilder
from tests.common import get_account_email

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_7')
logger.addHandler(logging.NullHandler())


@pytest.mark.full_test
@pytest.mark.columnar_test
@pytest.mark.order(7)
class TestColumnar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls. cluster_name = "pytest-columnar"
        cls.project_name = "pytest-project"
        cls.cidr = "0.0.0.0/0"
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
        if not self.cluster.id:
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
        self.allowed_cidr = ColumnarAllowedCIDR(self.cluster, self.cidr)
        if not self.allowed_cidr.id:
            builder = AllowedCIDRBuilder()
            builder.cidr(self.cidr)
            config = builder.build()
            self.allowed_cidr.create(config)
            assert self.allowed_cidr.id is not None

    def test_5(self):
        self.cluster.delete()

    def test_6(self):
        self.cluster.wait("destroying")
