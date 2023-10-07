from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.testclient import TestClient
from src.api import auth
from src import database as db
from src.constants import POTION_TYPES
from src.models import BarrelDelta
import logging

logger = logging.getLogger("barrels")

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

    barrel_delta = BarrelDelta.init_zero()
    gold_paid = 0

    for barrel in barrels_delivered:
        barrel_delta.add_stock(barrel.potion_type,barrel.ml_per_barrel, barrel.quantity)

        gold_paid += barrel.price * barrel.quantity

    db.add_gold(-gold_paid)
    db.add_barrel_stock(barrel_delta)

    logger.info(f"Recieved Barrels, paid {gold_paid} gold", extra={
        "ml_added_red": barrel_delta.red_ml,
        "ml_added_green": barrel_delta.green_ml,
        "ml_added_blue": barrel_delta.blue_ml,
        "ml_added_dark": barrel_delta.dark_ml,
        "gold_paid": gold_paid,
    })

    return "OK"

    
def buy_best_barrels(wholesale_catalog: list[Barrel], budget) -> list[dict]:
    '''Returns the SKU and Qty of Barrels to Buy'''
    barrels_to_buy = []
    budget = 500
    expected_value = 100 / 50 # in ml / $

    potential_barrels = []

    # Future: Take into account customer demand

    # first Cull any Barrels where we lose money
    for barrel in wholesale_catalog:
        barrel_value = barrel.ml_per_barrel / barrel.price 
        if barrel_value >= expected_value:
            potential_barrels.append(barrel)
        
    

    while budget > 0 and len(potential_barrels) > 0:
        for potion_type in POTION_TYPES:

            best_value = -1
            best_idx = None

            for (idx, barrel) in enumerate(potential_barrels):
                if potion_type != barrel.potion_type:
                    continue

                barrel_value = barrel.ml_per_barrel / barrel.price 
                
                if barrel_value > best_value:
                    best_idx = idx
                    best_value = barrel_value

            
            if best_idx is None:
                continue

            # Now we have best barrel of a certain typ
            best_barrel = potential_barrels.pop(best_idx)

            if best_barrel.price <= budget:
                existing_barrel = [x for x in barrels_to_buy 
                                   if x["sku"] == best_barrel.sku]

                if len(existing_barrel) > 0:
                    existing_barrel[0]["quantity"] += 1
                else:
                    barrels_to_buy.append(
                        {
                            "sku": best_barrel.sku,
                            "quantity": 1
                        }
                    )

                budget -= best_barrel.price

                best_barrel.quantity -= 1
                
                if best_barrel.quantity > 0:
                    potential_barrels.append(best_barrel)
    
    return barrels_to_buy
    

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    gold = db.get_gold()

    logger.info("Starting Barrel Planning", extra={
        "gold": gold
    })

    barrels_to_buy = buy_best_barrels(wholesale_catalog)
        
    if len(barrels_to_buy) == 0:
        logger.warning("We don't have enough money, can't buy anything")

    return barrels_to_buy