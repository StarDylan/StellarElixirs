### Tests ###
from fastapi.testclient import TestClient
from ..api.server import app
import json
import sys
sys.path.append(".")

client = TestClient(app)

def test_read_main():

    wholesale_catalog = '''[{"sku": "SMALL_RED_BARREL", "price": 100, "quantity": 10, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 500}, {"sku": "SMALL_GREEN_BARREL", "price": 100, "quantity": 10, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 500}, {"sku": "SMALL_BLUE_BARREL", "price": 120, "quantity": 10, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 500}, {"sku": "MINI_RED_BARREL", "price": 60, "quantity": 1, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 200}, {"sku": "MINI_GREEN_BARREL", "price": 60, "quantity": 1, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 200}, {"sku": "MINI_BLUE_BARREL", "price": 60, "quantity": 1, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 200}]'''  # noqa: E501

    response = client.post("/barrels/plan", content=wholesale_catalog)
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}