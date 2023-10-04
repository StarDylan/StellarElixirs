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
    potions_to_sell = db.get_potions()[:20]
    
    if len(potions_to_sell) == 0:
        print("No potions in inventory")
        return []
    else:
        catalog = []
        for potion_entry in potions_to_sell:
            catalog.append({
                "sku": potion_entry.sku,
                "name": potion_entry.sku,
                "quantity": potion_entry.quantity,
                "price": potion_entry.price,
                "potion_type": potion_entry.potion_type.to_array(),
            })
        
        return catalog
