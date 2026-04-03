from typing import Any

import pytest

from users.tests.factories import UserFactory


@pytest.fixture
def user(db: Any) -> Any:  # noqa: ARG001
    """
    Create the singleton admin user.
    In this app, there is only one user who is also the admin.
    """

    return UserFactory()


@pytest.fixture
def admin_client(client: Any, user: Any) -> Any:
    """Admin test client"""
    client.force_login(user)
    return client
