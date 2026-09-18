from fastapi.testclient import TestClient

from main import app


def test_seeded_food_and_customers_are_available():
    with TestClient(app) as client:
        foods = client.get("/food")
        customers = client.get("/customers")

    assert foods.status_code == 200
    assert len(foods.json()) >= 3
    assert customers.status_code == 200
    assert len(customers.json()) >= 3


def test_order_total_is_calculated_and_invalid_ids_are_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/orders",
            json={"customer_id": 1, "food_id": 1, "quantity": 2},
        )
        invalid = client.post(
            "/orders",
            json={"customer_id": 99999, "food_id": 1, "quantity": 1},
        )

    assert invalid.status_code == 404
    assert response.status_code == 201
    assert response.json()["total_amount"] == "25.00"
