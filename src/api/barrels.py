from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    red = 0
    gold_used = 0
    for barrel in barrels_delivered:
        red += barrel.ml_per_barrel * barrel.quantity

        gold_used += barrel.price * barrel.quantity

    existing_red_ml = db.get_red_ml()
    existing_gold = db.get_gold()

    db.add_gold(-gold_used)
    db.add_red_ml(red)

    print("Barrels Recieved!")
    print(f"Red ML go from {existing_red_ml} to {existing_red_ml + red}")
    print(f"Gold go from {existing_gold} to {existing_gold - gold_used}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    red_potions = db.get_red_potions()
    gold = db.get_gold()
    
    print("Wholesale Catalog Recieved!")
    print(f"num_red_potions: {red_potions}; Gold: {gold}")
    if red_potions < 10 and gold >= 100:
        print("Buy SMALL_RED_BARREL")
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
    
        
    else:
        print("Buy Nothing")
        return []
