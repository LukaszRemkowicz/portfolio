import pytest

from programming.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestProgrammingModels:
    def test_project_str(self):
        """Verify Project string representation"""
        project = ProjectFactory(name="Alpha Project")
        assert str(project) == "Alpha Project"
