#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.user import CapellaUser
from tests.common import get_account_email

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_2')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestUser(object):
    email = get_account_email()

    @classmethod
    def setup_class(cls):
        if not cls.email:
            raise RuntimeError('account email not set')

    @classmethod
    def teardown_class(cls):
        pass

    def test_1(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        users = CapellaUser(org, self.email)
        result = users.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_2(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        user = CapellaUser(org, self.email)
        user_id = user.id
        result = user.get(user_id)
        assert result.id is not None
        assert result.id == user_id
        logger.debug(f"User email: {self.email} id: {user_id}")
