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
    project = "pytest-project"
    project_id = None
    email = get_account_email()

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_1(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org)

        current_projects = project.list_by_user(self.email)
        for project in current_projects:
            if project.name == self.project:
                logger.debug(f"Project {project.name} already exists")
                return

        builder = CapellaProjectBuilder()
        builder = builder.name(self.project)
        config = builder.build()
        result = project.create(config)
        assert result is not None
        self.project_id = result

        user = CapellaUser(org, self.email)
        user.set_project_owner(self.project_id)

    def test_2(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, self.project)
        result = project.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_3(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, self.project)
        project_id = project.id
        result = project.get(project_id)
        assert result.id is not None
        assert result.id == project_id
