import uuid

from tests.conftest import auth_headers


def _place_order(client, user_id: int, product_id: int = 1, quantity: int = 1):
    headers = auth_headers(user_id=user_id)
    client.post("/cart/items", json={"product_id": product_id, "quantity": quantity}, headers=headers)
    return client.post(
        "/checkout", json={"idempotency_key": str(uuid.uuid4())}, headers=headers
    ).json()


def test_stats_requires_admin(client):
    response = client.get("/admin/stats", headers=auth_headers(user_id=1, is_admin=False))
    assert response.status_code == 403


def test_stats_reflects_orders_placed(client):
    _place_order(client, user_id=1, product_id=1, quantity=2)
    _place_order(client, user_id=2, product_id=2, quantity=1)

    response = client.get("/admin/stats", headers=auth_headers(user_id=999, is_admin=True))
    assert response.status_code == 200
    body = response.json()
    assert body["total_orders"] == 2
    assert body["total_items_purchased"] == 3
    assert body["total_revenue"] > 0
    assert body["total_discount_amount"] == 0
    assert body["discount_codes"] == []
