import pytest

from programming.models import ProgrammingPageConfig
from programming.tests.factories import ProgrammingPageConfigFactory, ProjectFactory


@pytest.mark.django_db
class TestProgrammingModels:
    def test_project_str(self):
        """Verify Project string representation"""
        project = ProjectFactory(name="Alpha Project")
        assert str(project) == "Alpha Project"

    def test_programming_page_config_str(self):
        """Verify ProgrammingPageConfig string representation"""
        config = ProgrammingPageConfigFactory(enabled=True)
        assert str(config) == "Programming Page Config (Enabled: True)"

    def test_programming_page_config_singleton_save(self):
        """Verify that multiple instances cannot be created via save()"""
        ProgrammingPageConfig.objects.all().delete()

        ProgrammingPageConfigFactory(enabled=True)
        assert ProgrammingPageConfig.objects.count() == 1

        # Try to save another instance without PK (should raise ValueError)
        config2 = ProgrammingPageConfigFactory.build(pk=None, enabled=False)
        with pytest.raises(ValueError, match="Only one config is allowed"):
            config2.save()
        assert ProgrammingPageConfig.objects.count() == 1

    def test_programming_page_config_get_config(self):
        """Verify get_config singleton behavior"""
        ProgrammingPageConfig.objects.all().delete()
        config = ProgrammingPageConfig.get_config()
        assert config.pk == 1
