#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.logic.project import CapellaProjectBuilder
from libcapella.user import CapellaUser
from tests.common import get_account_email

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_2')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestProject(object):
    project_name = "pytest-project"
    project = None
    org = None
    email = get_account_email()

    @classmethod
    def setup_class(cls):
        if not cls.email:
            raise RuntimeError('account email not set')
        config = CapellaConfig(profile="pytest")
        cls.org = CapellaOrganization(config)
        cls.project = CapellaProject(cls.org, cls.project_name, cls.email)

    @classmethod
    def teardown_class(cls):
        pass

    def test_1(self):
        if self.project.id:
            logger.debug(f"Project {self.project_name} already exists")
            return

        builder = CapellaProjectBuilder()
        builder = builder.name(self.project_name)
        config = builder.build()
        self.project.create(config)
        assert self.project.id is not None

        user = CapellaUser(self.org, self.email)
        user.set_project_owner(self.project.id)

    def test_2(self):
        result = self.project.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_3(self):
        project_id = self.project.id
        result = self.project.get(project_id)
        assert result.id is not None
        assert result.id == project_id
