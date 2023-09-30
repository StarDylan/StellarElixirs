from fastapi import APIRouter
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    print("Customer Getting catalog")

    # Can return a max of 20 items.
    num_red_potions = db.get_red_potions()
    
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
