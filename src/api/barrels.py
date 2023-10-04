from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.models import BarrelDelta

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

    barrel_delta = BarrelDelta.init_zero()
    gold_paid = 0

    for barrel in barrels_delivered:
        barrel_delta.add_stock(barrel.potion_type, barrel.quantity)

        gold_paid += barrel.price * barrel.quantity

    db.add_gold(-gold_paid)
    db.add_barrel_stock(barrel_delta)

    print("Barrels Recieved!")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)


    gold = db.get_gold()
    
    print("Wholesale Catalog Recieved!")

    if gold >= 100 and gold < 300:
        print("Buy SMALL_RED_BARREL")
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            },
        ]

    if gold >= 300:
        print("Buy ALL COLORS")
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            },
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            },
            {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
            },
        ]
    
        
    else:
        print("Buy Nothing")
        return []
