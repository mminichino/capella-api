#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_2')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestProject(object):
    project = "pytest-project"

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
        result = project.list()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_2(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, self.project)
        project_id = project.id
        result = project.get(project_id)
        assert result.id is not None
        assert result.id == project_id
