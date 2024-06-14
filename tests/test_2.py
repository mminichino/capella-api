#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.project import CapellaProject

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_2')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestProject(object):

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_1(self):
        config = CapellaConfig(project="pytest-project", profile="pytest")
        project = CapellaProject(config)
        result = project.list_projects()
        assert len(result) >= 1
        assert result[0].id is not None

    def test_2(self):
        config = CapellaConfig(project="pytest-project", profile="pytest")
        project = CapellaProject(config)
        project_id = project.id
        result = project.get_project(project_id)
        assert result.id is not None
        assert result.id == project_id
