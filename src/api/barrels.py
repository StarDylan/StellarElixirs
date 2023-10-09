from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.models import BarrelDelta
import logging
import math

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

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    gold = db.get_gold()
    potions = db.get_potions()

    barrels_to_buy = []

    budget = gold * 5
    

    while budget > 0 and len(potions) > 0:
        # Find the most difference between desired_qty and current_qty
        most_difference_ratio = None
        most_difference_potion = None
        for potion in potions[:]:
            ratio = potion.quantity / potion.desired_qty 
            if ratio >= 1.0:
                potions.remove(potion) 
                continue
            if most_difference_potion is None or ratio > most_difference_ratio:
                most_difference_potion = potion
                most_difference_ratio = ratio
        
        if most_difference_potion is None:
            break

        # Remove from consideration
        potions.remove(most_difference_potion)

        potion = most_difference_potion
        # Determine how much ml we need
        barrel_ml_required = potion.potion_type * (potion.desired_qty - potion.quantity)
        print(potion)
        print(f"barrel_ml_required: {barrel_ml_required.to_array()}")

        
        # If we have less than 10% of the desired qty, get 10% of the desired qty at any price
        # Must be sorted!
        balking_ratio_and_amount = [
            (15, 1 * potion.desired_qty),
            (8, 0.5 * potion.desired_qty),
            (0, 0.1 * potion.desired_qty)
            ]
        
        balking_ratio = None        
        for balk_ratio, balk_amount in balking_ratio_and_amount:
            if potion.quantity < balk_amount:
                balking_ratio = balk_ratio
                break


        for potion_type in range(0,4):
            if barrel_ml_required.to_array()[potion_type] > 0:

                # Find Best Barrel for the ml we require
                best_barrel = None
                best_barrel_ratio = None
                for barrel in wholesale_catalog:
                    if barrel.potion_type[potion_type] == 0:
                        continue
                    ratio = barrel.ml_per_barrel / barrel.price
                    if best_barrel is None or ratio > best_barrel_ratio:
                        best_barrel = barrel
                        best_barrel_ratio = ratio
                
                if best_barrel is None:
                    continue

                # Determine how many barrels we need
                barrels_required = max(1, math.ceil(barrel_ml_required.to_array()[potion_type] / best_barrel.ml_per_barrel))  # noqa: E501
                print(f"barrels_required: {barrels_required}")
                
                chosen_balk_amount = 0
                for balk_ratio, balk_amount in balking_ratio_and_amount:

                    if best_barrel_ratio < balk_ratio:
                        chosen_balk_amount = balk_amount
                        break

                # Determine how much we can spend and how many barrels we can buy
                price_to_spend = min(barrels_required * best_barrel.price, budget)
                barrels_to_buy_qty = min(price_to_spend // best_barrel.price, best_barrel.quantity)  # noqa: E501
                print(f"barrels_to_buy_qty: {barrels_to_buy_qty}")

                if barrels_to_buy_qty > 0:

                   
                    
                    if best_barrel_ratio < balking_ratio:
                        continue

                    # Update the catalog
                    best_barrel.quantity -= barrels_to_buy_qty

                    barrels_to_buy.append({
                        "sku": best_barrel.sku,
                        "quantity": barrels_to_buy_qty,
                    })

                    budget -= price_to_spend

    


    logger.info("Starting Barrel Planning", extra={
        "gold": gold
    })


    return barrels_to_buy