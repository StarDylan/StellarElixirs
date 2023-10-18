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

    db.add_gold(-gold_paid, "Barrel Delivery")
    db.add_barrel_stock(barrel_delta, "Barrel Delivery")

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

    
    db.add_historical_catalog_data(wholesale_catalog)
    
    gold = db.get_gold()

    barrel_stock_delta = BarrelDelta.init_zero()
    barrel_stock_delta.add_stock(db.get_barrel_stock().to_array(), 1, 1)

    barrels_to_buy = []

    starting_budget = gold * 0.5

    budget = starting_budget
    
    barrel_history_record = []

    barrel_target_amount = 30000

    barrel_types = [
        [0,0,0,1],
        [1,0,0,0],
        [0,1,0,0],
        [0,0,1,0],
    ]

    while budget > 0 and len(wholesale_catalog) > 0 and len(barrel_types) > 0:
        # Find the most difference between target and current
        most_difference_ratio = None
        most_difference_barrel_type = None
        for barrel_type in barrel_types[:]:
            idx = barrel_type.index(1)

            ratio = barrel_stock_delta.to_array()[idx] / barrel_target_amount 
            if ratio >= 1.0:
                barrel_types.remove(barrel_type)
                continue
            if most_difference_ratio is None or ratio < most_difference_ratio:
                most_difference_barrel_type = barrel_type
                most_difference_ratio = ratio
        
        if most_difference_barrel_type is None:
            break

        barrel_type_idx = most_difference_barrel_type.index(1)
        # Determine how much ml we need


        # Find Best Barrel for the ml we require
        best_barrel = None
        best_barrel_ratio = None
        for barrel in wholesale_catalog[:]:
            if barrel.potion_type[barrel_type_idx] == 0:
                continue
            if barrel.price > budget:
                wholesale_catalog.remove(barrel)
                continue
            ratio = barrel.ml_per_barrel / barrel.price
            if best_barrel is None or ratio > best_barrel_ratio:
                best_barrel = barrel
                best_barrel_ratio = ratio
        
        if best_barrel is None:
            barrel_types.remove(most_difference_barrel_type)
            continue

              
        # If we have less than 20% of the desired qty, try to buy more but not below
        # What we can sell them at (50g per 100ml (2))
        # Must be sorted!
        balking_ratio_and_amount = [
            (15, 1 * barrel_target_amount),
            (8, 0.3 * barrel_target_amount),
            (2, 0.2 * barrel_target_amount)
            ]
        
        best_balking_ratio = None  
        balking_amount = None      
        for balk_ratio_temp, balk_amount_temp in balking_ratio_and_amount:
            if balk_ratio_temp <= best_barrel_ratio and (best_balking_ratio is None or balk_ratio_temp > best_balking_ratio):
                best_balking_ratio = balk_ratio_temp
                balking_amount = balk_amount_temp
        
        barrel_ml_requested = min(balking_amount - barrel_stock_delta.to_array()[barrel_type_idx], balking_amount)  # noqa: E501
        if barrel_ml_requested < 0:
            barrel_types.remove(most_difference_barrel_type)
            continue

        # Determine how many barrels we need
        barrels_required = math.ceil(barrel_ml_requested / best_barrel.ml_per_barrel)  # noqa: E501



        # Determine how much we can spend and how many barrels we can buy
        price_to_spend = min(barrels_required * best_barrel.price, budget)

        barrels_to_buy_qty = min(price_to_spend // best_barrel.price, best_barrel.quantity)  # noqa: E501

        if barrels_to_buy_qty > 0:
            # Update the catalog
            best_barrel.quantity -= barrels_to_buy_qty
            if best_barrel.quantity <= 0:
                wholesale_catalog.remove(best_barrel)


            type_to_add = [0,0,0,0]
            type_to_add[barrel_type_idx] = 1

            barrel_stock_delta.add_stock(type_to_add, best_barrel.ml_per_barrel, barrels_to_buy_qty)

            barrel_history_record.append(db.BarrelPlanEntry(best_barrel.sku,
                barrels_to_buy_qty, best_barrel.ml_per_barrel, best_barrel.price,
                best_barrel.potion_type))

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

    db.add_barrel_history(barrel_history_record)
            

    return barrels_to_buy