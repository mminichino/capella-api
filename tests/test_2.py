#!/usr/bin/env python3

import logging
import pytest
import warnings
import unittest
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.user import CapellaUser
from tests.common import get_account_email

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_2')
logger.addHandler(logging.NullHandler())


@pytest.mark.full_test
@pytest.mark.user_test
@pytest.mark.order(2)
class TestUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.email = get_account_email()
        if not cls.email:
            raise RuntimeError('account email not set')
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        cls.user = CapellaUser(org, cls.email)
        logger.debug("User test setup complete")

    @classmethod
    def tearDownClass(cls):
        pass

    def test_1(self):
        result = self.user.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_2(self):
        user_id = self.user.id
        assert user_id is not None
        result = self.user.get(user_id)
        assert result.id is not None
        assert result.id == user_id
        logger.debug(f"User email: {self.email} id: {user_id}")
