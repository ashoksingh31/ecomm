from tests.conftest import auth_headers


def test_add_item_to_cart(client):
    headers = auth_headers(user_id=1)
    response = client.post("/cart/items", json={"product_id": 1, "quantity": 2}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["items"][0]["quantity"] == 2
    assert body["subtotal"] > 0


def test_adding_same_product_twice_accumulates_quantity(client):
    headers = auth_headers(user_id=1)
    client.post("/cart/items", json={"product_id": 1, "quantity": 2}, headers=headers)
    response = client.post("/cart/items", json={"product_id": 1, "quantity": 3}, headers=headers)
    assert response.json()["items"][0]["quantity"] == 5


def test_add_nonexistent_product_fails(client):
    headers = auth_headers(user_id=1)
    response = client.post("/cart/items", json={"product_id": 9999, "quantity": 1}, headers=headers)
    assert response.status_code == 404


def test_add_zero_quantity_rejected(client):
    headers = auth_headers(user_id=1)
    response = client.post("/cart/items", json={"product_id": 1, "quantity": 0}, headers=headers)
    assert response.status_code == 422  # pydantic validation (gt=0)


def test_update_cart_item_quantity(client):
    headers = auth_headers(user_id=1)
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers)
    response = client.patch("/cart/items/1", json={"quantity": 10}, headers=headers)
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 10


def test_update_item_not_in_cart_returns_404(client):
    headers = auth_headers(user_id=1)
    response = client.patch("/cart/items/1", json={"quantity": 5}, headers=headers)
    assert response.status_code == 404


def test_remove_cart_item(client):
    headers = auth_headers(user_id=1)
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers)
    response = client.delete("/cart/items/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_carts_are_isolated_per_user(client):
    client.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=auth_headers(user_id=1))
    response = client.get("/cart", headers=auth_headers(user_id=2))
    assert response.json()["items"] == []
