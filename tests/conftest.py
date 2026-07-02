"""
Shared pytest fixtures.

Each test gets fresh in-memory repositories via deps.reset_state(), so
tests never leak cart/order/coupon state into each other even though the
app uses process-wide singletons in production.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.deps import reset_state
from src.core.security import create_access_token
from src.main import app


@pytest.fixture
def client():
    reset_state()
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(user_id: int, is_admin: bool = False) -> dict:
    token = create_access_token(user_id=user_id, is_admin=is_admin)
    return {"Authorization": f"Bearer {token}"}
