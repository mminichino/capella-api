#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_1')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestOrganization(object):

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_1(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        result = org.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_2(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        org_list = org.list()
        result = org.get(org_list[0].id)
        assert result.id is not None
        assert result.id == org_list[0].id
