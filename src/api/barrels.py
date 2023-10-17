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

    logger.info(f"Received Barrels, paid {gold_paid} gold", extra={
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

    barrel_stock_delta = BarrelDelta.init_zero()
    barrel_stock_delta.add_stock(db.get_barrel_stock().to_array(), 1, 1)

    barrels_to_buy = []

    starting_budget = gold * 0.5

    budget = starting_budget

    excess = BarrelDelta.init_zero()

    while budget > 0 and len(potions) > 0:
        # Find the most difference between desired_qty and current_qty
        most_difference_ratio = None
        most_difference_potion = None
        for potion in potions[:]:
            ratio = potion.quantity / potion.desired_qty 
            if ratio >= 1.0:
                potions.remove(potion) 
                continue
            if most_difference_potion is None or ratio < most_difference_ratio:
                most_difference_potion = potion
                most_difference_ratio = ratio
        
        if most_difference_potion is None:
            break

        # Remove from consideration
        potions.remove(most_difference_potion)

        potion = most_difference_potion
        # Determine how much ml we need

        
        # If we have less than 10% of the desired qty, try to buy more but not below
        # What we can sell them at (50g per 100ml (2))
        # Must be sorted!
        balking_ratio_and_amount = [
            (15, 1 * potion.desired_qty),
            (8, 0.3 * potion.desired_qty),
            (2, 0.2 * potion.desired_qty)
            ]
        
        balking_ratio = None  
        balking_amount = None      
        for balk_ratio_temp, balk_amount in balking_ratio_and_amount:
            if potion.quantity < balk_amount:
                balking_ratio = balk_ratio_temp
                balking_amount = balk_amount
        
        potions_required = min((potion.desired_qty - potion.quantity), balking_amount)
        barrel_ml_required = potion.potion_type * potions_required
            


        for potion_type in range(0,4):
            if barrel_ml_required.to_array()[potion_type] > 0:
                
                if barrel_ml_required.to_array()[potion_type] <= excess.to_array()[potion_type]: # noqa: E501
                    type_to_remove = [0,0,0,0]
                    type_to_remove[potion_type] = 1
                    excess.remove_stock(type_to_remove, barrel_ml_required.to_array()[potion_type]) # noqa: E501
                    continue

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
               
                if best_barrel_ratio < balking_ratio:
                    continue

                # Determine how much we can spend and how many barrels we can buy
                price_to_spend = min(barrels_required * best_barrel.price, budget)
                barrels_to_buy_qty = min(price_to_spend // best_barrel.price, best_barrel.quantity)  # noqa: E501
                
                # Determine if we already have stock
                if barrel_stock_delta.to_array()[potion_type] >= best_barrel.ml_per_barrel * barrels_to_buy_qty:  # noqa: E501
                    barrel_to_stock_type = [0,0,0,0]
                    barrel_to_stock_type[potion_type] = 1
                    barrel_stock_delta.remove_stock(barrel_to_stock_type, best_barrel.ml_per_barrel * barrels_to_buy_qty)  # noqa: E501
                    continue

                if barrels_to_buy_qty > 0:
                    # Update the catalog
                    best_barrel.quantity -= barrels_to_buy_qty
                    if best_barrel.quantity <= 0:
                        wholesale_catalog.remove(best_barrel)


                    type_to_add = [0,0,0,0]
                    type_to_add[potion_type] = 1

                    # Keep track of any excess
                    excess.add_stock(type_to_add, best_barrel.ml_per_barrel, barrels_to_buy_qty)  # noqa: E501
                    excess.remove_stock(type_to_add, barrel_ml_required[potion_type]) # noqa: E501
                    excess.zero_if_negative() # In case didn't buy enough to meet required amount of potion quantity # noqa: E501

                    # Update the barrels to buy if sku already in list
                    for barrel in barrels_to_buy:
                        if barrel["sku"] == best_barrel.sku:
                            barrel["quantity"] += barrels_to_buy_qty
                            break
                    else:
                        barrels_to_buy.append({
                            "sku": best_barrel.sku,
                            "quantity": barrels_to_buy_qty,
                        })

                    budget -= price_to_spend
    
    if len(barrels_to_buy) == 0:
        logger.warning("Not buying any barrels")

    # Calculate total price
    total_price = 0
    for barrel in barrels_to_buy:
        for catalog_barrel in wholesale_catalog:
            if catalog_barrel.sku == barrel["sku"]:
                total_price += catalog_barrel.price * barrel["quantity"]
                break

    logger.info("Finished Barrel Planning", extra={
        "gold": gold,
        "budget": starting_budget,
        "gold_paid": total_price,
        "buying_barrels": barrels_to_buy,
    })

    return barrels_to_buy