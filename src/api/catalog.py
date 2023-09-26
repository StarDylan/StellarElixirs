from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    print("Customer Getting catalog")

    # Can return a max of 20 items.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT (num_red_potions) FROM global_inventory"))
        num_red_potions = result.one()[0]
        if num_red_potions == 0:
            print("No red potions in inventory")
            return []
        else:
            print("Red potions in inventory")
            return [
                    {
                        "sku": "RED_POTION_0",
                        "name": "red potion",
                        "quantity": num_red_potions,
                        "price": 50,
                        "potion_type": [100, 0, 0, 0],
                    }
            ]
