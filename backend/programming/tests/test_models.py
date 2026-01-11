import pytest

from programming.models import ProgrammingPageConfig, Project


@pytest.mark.django_db
class TestProgrammingModels:
    def test_project_str(self):
        """Verify Project string representation"""
        project = Project.objects.create(
            name="Alpha Project", description="Lorum Ipsum", technologies="Python"
        )
        assert str(project) == "Alpha Project"

    def test_programming_page_config_str(self):
        """Verify ProgrammingPageConfig string representation"""
        config = ProgrammingPageConfig.get_config()
        config.enabled = True
        assert str(config) == "Programming Page Config (Enabled: True)"

    def test_programming_page_config_singleton_save(self):
        """Verify that multiple instances cannot be created via save()"""
        ProgrammingPageConfig.objects.all().delete()

        config1 = ProgrammingPageConfig(pk=None, enabled=True)
        config1.save()
        assert ProgrammingPageConfig.objects.count() == 1

        # Try to save another instance without PK
        config2 = ProgrammingPageConfig(pk=None, enabled=False)
        config2.save()  # This should return early due to singleton logic
        assert ProgrammingPageConfig.objects.count() == 1

    def test_programming_page_config_get_config(self):
        """Verify get_config singleton behavior"""
        ProgrammingPageConfig.objects.all().delete()
        config = ProgrammingPageConfig.get_config()
        assert config.pk == 1
