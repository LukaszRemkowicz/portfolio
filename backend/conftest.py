# backend/conftest.py
"""
Root conftest.py for pytest
Imports shared fixtures from core.fixtures
"""

# Import all fixtures from core.fixtures to make them available globally
from core.fixtures import *  # noqa: F401,F403
