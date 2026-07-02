import uuid

from tests.conftest import auth_headers


def _checkout(client, headers, idempotency_key=None, discount_code=None):
    payload = {"idempotency_key": idempotency_key or str(uuid.uuid4())}
    if discount_code:
        payload["discount_code"] = discount_code
    return client.post("/checkout", json=payload, headers=headers)


def test_checkout_empty_cart_fails(client):
    response = _checkout(client, auth_headers(user_id=1))
    assert response.status_code == 400


def test_successful_checkout(client):
    headers = auth_headers(user_id=1)
    client.post("/cart/items", json={"product_id": 1, "quantity": 2}, headers=headers)

    response = _checkout(client, headers)
    assert response.status_code == 201
    body = response.json()
    assert body["sequence_number"] == 1
    assert body["total"] == body["subtotal"]
    assert body["discount_amount"] == 0


def test_checkout_clears_the_cart(client):
    headers = auth_headers(user_id=1)
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers)
    _checkout(client, headers)

    response = client.get("/cart", headers=headers)
    assert response.json()["items"] == []


def test_idempotent_checkout_returns_same_order(client):
    headers = auth_headers(user_id=1)
    key = str(uuid.uuid4())

    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers)
    first = _checkout(client, headers, idempotency_key=key)

    # Cart is empty now, but re-using the same key must still succeed and
    # return the SAME order rather than failing on "empty cart".
    second = _checkout(client, headers, idempotency_key=key)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_sequence_numbers_increment_across_users(client):
    h1 = auth_headers(user_id=1)
    h2 = auth_headers(user_id=2)

    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=h1)
    order1 = _checkout(client, h1).json()

    client.post("/cart/items", json={"product_id": 2, "quantity": 1}, headers=h2)
    order2 = _checkout(client, h2).json()

    assert order1["sequence_number"] == 1
    assert order2["sequence_number"] == 2


def test_checkout_with_invalid_discount_code_fails(client):
    headers = auth_headers(user_id=1)
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers)
    response = _checkout(client, headers, discount_code="DOESNOTEXIST")
    assert response.status_code == 404
