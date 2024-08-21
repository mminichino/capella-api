#!/usr/bin/env python3

import logging
import pytest
import warnings
from libcapella.config import CapellaConfig
from libcapella.organization import CapellaOrganization
from libcapella.project import CapellaProject
from libcapella.columnar import CapellaColumnar
from libcapella.logic.columnar import CapellaColumnarBuilder

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_4')
logger.addHandler(logging.NullHandler())


@pytest.mark.serial
class TestProject(object):
    project = "pytest-project"
    columnar_id = None

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
        columnar = CapellaColumnar(project)

        builder = CapellaColumnarBuilder("aws")
        builder = builder.name("pytest-columnar")
        builder = builder.description("Pytest created cluster")
        builder = builder.region("us-east-1")
        builder = builder.compute("4x32", 4)
        config = builder.build()
        result = columnar.create(config)
        assert result is not None
        self.columnar_id = result

    def test_2(self):
        config = CapellaConfig(profile="pytest")
        org = CapellaOrganization(config)
        project = CapellaProject(org, self.project)
        columnar = CapellaColumnar(project, "pytest-columnar")
        columnar_id = columnar.id
        result = columnar.get(columnar_id)
        assert result.id is not None
        assert result.id == columnar_id
