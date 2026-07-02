import uuid

from src.config.settings import settings
from tests.conftest import auth_headers


def _place_order(client, user_id: int, product_id: int = 1, quantity: int = 1):
    headers = auth_headers(user_id=user_id)
    client.post("/cart/items", json={"product_id": product_id, "quantity": quantity}, headers=headers)
    return client.post(
        "/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=headers
    ).json()


def test_generate_before_milestone_reached_returns_409(client):
    admin_headers = auth_headers(user_id=999, is_admin=True)
    # Only place (N - 1) orders, milestone not reached yet.
    for i in range(settings.milestone_interval - 1):
        _place_order(client, user_id=i + 1)

    response = client.post("/admin/discount-codes/generate", headers=admin_headers)
    assert response.status_code == 409


def test_generate_awards_code_to_triggering_user_only(client):
    admin_headers = auth_headers(user_id=999, is_admin=True)
    n = settings.milestone_interval

    last_order = None
    for i in range(n):
        last_order = _place_order(client, user_id=i + 1)

    response = client.post("/admin/discount-codes/generate", headers=admin_headers)
    assert response.status_code == 200
    generated = response.json()["generated"]
    assert len(generated) == 1
    assert generated[0]["owner_user_id"] == last_order["user_id"]
    assert generated[0]["milestone"] == 1


def test_non_admin_cannot_generate_codes(client):
    for i in range(settings.milestone_interval):
        _place_order(client, user_id=i + 1)

    response = client.post(
        "/admin/discount-codes/generate", headers=auth_headers(user_id=1, is_admin=False)
    )
    assert response.status_code == 403


def test_code_redeemable_only_by_owner(client):
    admin_headers = auth_headers(user_id=999, is_admin=True)
    n = settings.milestone_interval
    for i in range(n):
        last_order = _place_order(client, user_id=i + 1)

    code = client.post("/admin/discount-codes/generate", headers=admin_headers).json()["generated"][0]["code"]
    owner_id = last_order["user_id"]
    other_id = owner_id + 100  # guaranteed to be a different user

    other_headers = auth_headers(user_id=other_id)
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=other_headers)
    response = client.post(
        "/checkout",
        json={"idempotency_key": str(uuid.uuid4()), "discount_code": code},
        headers=other_headers,
    )
    assert response.status_code == 403


def test_code_applies_discount_and_is_single_use(client):
    admin_headers = auth_headers(user_id=999, is_admin=True)
    n = settings.milestone_interval
    for i in range(n):
        last_order = _place_order(client, user_id=i + 1)

    code = client.post("/admin/discount-codes/generate", headers=admin_headers).json()["generated"][0]["code"]
    owner_id = last_order["user_id"]
    owner_headers = auth_headers(user_id=owner_id)

    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=owner_headers)
    first = client.post(
        "/checkout",
        json={"idempotency_key": str(uuid.uuid4()), "discount_code": code},
        headers=owner_headers,
    )
    assert first.status_code == 201
    assert first.json()["discount_amount"] > 0

    # Try to reuse the same code on a brand new order.
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=owner_headers)
    second = client.post(
        "/checkout",
        json={"idempotency_key": str(uuid.uuid4()), "discount_code": code},
        headers=owner_headers,
    )
    assert second.status_code == 400


def test_catch_up_generation_awards_multiple_milestones_at_once(client):
    admin_headers = auth_headers(user_id=999, is_admin=True)
    n = settings.milestone_interval
    # Place 2*N orders without ever calling generate in between.
    for i in range(2 * n):
        _place_order(client, user_id=i + 1)

    response = client.post("/admin/discount-codes/generate", headers=admin_headers)
    generated = response.json()["generated"]
    assert len(generated) == 2
    assert {g["milestone"] for g in generated} == {1, 2}
