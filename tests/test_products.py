from tests.conftest import auth_headers


def test_list_products_requires_auth(client):
    response = client.get("/products")
    assert response.status_code == 401


def test_list_products(client):
    response = client.get("/products", headers=auth_headers(user_id=1))
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert "price" in body[0]


def test_get_single_product(client):
    response = client.get("/products/1", headers=auth_headers(user_id=1))
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_nonexistent_product_returns_404(client):
    response = client.get("/products/9999", headers=auth_headers(user_id=1))
    assert response.status_code == 404
