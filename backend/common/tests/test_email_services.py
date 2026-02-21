from common.services import BaseEmailService


class ConcreteEmailService(BaseEmailService):
    """Concrete implementation for testing BaseEmailService."""

    def get_subject(self) -> str:
        return "Test Subject"

    def get_context(self) -> dict:
        return {"variable": "value"}

    def get_template_name(self) -> str:
        return "test/template.html"


class TestBaseEmailService:
    """Test suite for BaseEmailService template method pattern."""

    def test_send_email_flow(self, mocker):
        """Test that send_email orchestrates the workflow correctly."""
        # Setup
        mock_render = mocker.patch(
            "common.services.render_to_string", return_value="<html>Rendered Content</html>"
        )
        mock_send_async = mocker.patch("common.services.EmailService.send_async")

        service = ConcreteEmailService()

        # Execute
        service.send_email()

        # Verify
        # 1. Template rendered with correct name and context
        mock_render.assert_called_once_with("test/template.html", {"variable": "value"})

        # 2. Email dispatched with correct subject and content
        mock_send_async.assert_called_once_with("Test Subject", "<html>Rendered Content</html>")
