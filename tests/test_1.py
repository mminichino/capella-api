#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_1')
logger.addHandler(logging.NullHandler())


@pytest.mark.org_test
@pytest.mark.order(1)
class TestOrganization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = CapellaConfig(profile="pytest")
        cls.org = CapellaOrganization(cls.config)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        result = self.org.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_2(self):
        org_list = self.org.list()
        result = self.org.get(org_list[0].id)
        assert result.id is not None
        assert result.id == org_list[0].id
