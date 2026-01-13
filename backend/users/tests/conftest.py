from typing import Any

import pytest


@pytest.fixture
def user(db: Any) -> Any:
    """
    Create the singleton admin user.
    In this app, there is only one user who is also the admin.
    """
    from users.tests.factories import UserFactory

    return UserFactory()


@pytest.fixture
def admin_client(client: Any, user: Any) -> Any:
    """Admin test client"""
    client.force_login(user)
    return client
