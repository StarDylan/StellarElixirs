from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.models import BarrelDelta, PotionType
import logging

logger = logging.getLogger("bottler")

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    barrel_delta = BarrelDelta.init_zero()
    
    for delivered_potion in potions_delivered:
        db.add_potions_by_type(
            PotionType.from_array(delivered_potion.potion_type), 
            delivered_potion.quantity)

        barrel_delta.remove_stock(delivered_potion.potion_type, 
                                  delivered_potion.quantity)

    db.add_barrel_stock(barrel_delta)

    logger.info("Recieved Bottles", extra={
        "ml_used_red": -barrel_delta.red_ml,
        "ml_used_green": -barrel_delta.green_ml,
        "ml_used_blue": -barrel_delta.blue_ml,
        "ml_used_dark": -barrel_delta.dark_ml,
    })

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.


    barrel_stock = BarrelDelta.init_zero()
    barrel_stock.add_stock(db.get_barrel_stock().to_array(), 1, 1)

    starting_stock = barrel_stock.to_array()


    potions = db.get_potions()

    bottle_plan = []

    total_potions = 0
    for potion in potions:
        total_potions += potion.quantity


    # Get the potion with the least ratio of stock 
    while len(potions) > 0 and (barrel_stock.red_ml >= 100 
                                or barrel_stock.green_ml >= 100 
                                or barrel_stock.blue_ml >= 100 
                                or barrel_stock.dark_ml >= 100):
        least_ratio = None
        least_ratio_potion = None
        for potion in potions:
            ratio = potion.quantity / potion.desired_qty

            if least_ratio is None or ratio < least_ratio:
                least_ratio = ratio
                least_ratio_potion = potion
        
        # TAKEN FROM BARREL

        balking_ratio_and_amount = [
            (15, 1 * potion.desired_qty),
            (8, 0.3 * potion.desired_qty),
            (2, 0.2 * potion.desired_qty)
            ]
        
        balking_amount = None      
        for balk_ratio_temp, balk_amount in balking_ratio_and_amount:
            if least_ratio_potion.quantity < balk_amount:
                balking_amount = balk_amount
        

        potions.remove(least_ratio_potion)

        if balk_amount is None:
            continue # Don't need to bottle

        # Determine how much we can bottle

        potions_want_to_make = min(balking_amount, least_ratio_potion.desired_qty - least_ratio_potion.quantity)  # noqa: E501

        print(f"balking amount: {balking_amount}")
        print("potions_want_to_make", potions_want_to_make)
        print("least_ratio_potion", least_ratio_potion)
        print("Balking ratio and amount", balking_ratio_and_amount)

        potions_can_make = potions_want_to_make
        for color_required, color_stock in zip(least_ratio_potion.potion_type.to_array(), barrel_stock.to_array()):  # noqa: E501
            if color_required == 0:
                continue
            potions_can_make = min(potions_can_make, color_stock // color_required)


        
        

        potion_limit_number = max(300-total_potions, 0)

        potions_can_make = min(potion_limit_number, potions_can_make)

        total_potions += potions_can_make
        
        if potions_can_make == 0:
            continue

        bottle_plan.append(
                {
                    "potion_type": least_ratio_potion.potion_type.to_array(),
                    "quantity": int(potions_can_make),
                }
        )

        barrel_stock.remove_stock(least_ratio_potion.potion_type.to_array(), potions_can_make)  # noqa: E501
            

    if len(bottle_plan) == 0:
        logger.info("Not bottling", extra={
            "ml_red": starting_stock[0],
            "ml_green": starting_stock[1],
            "ml_blue": starting_stock[2],
            "ml_dark": starting_stock[3],
        })
    else:
        logger.info("Planned Bottles", extra={
            "ml_red": starting_stock[0],
            "ml_green": starting_stock[1],
            "ml_blue": starting_stock[2],
            "ml_dark": starting_stock[3],
            "bottle_plan": bottle_plan
        })

    
    return bottle_plan
