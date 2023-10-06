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
            PotionType.from_list(delivered_potion.potion_type), 
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


    barrel_stock = db.get_barrel_stock()

    logger.info("Starting Bottle Planning", extra={
        "ml_red": barrel_stock.red_ml,
        "ml_green": barrel_stock.green_ml,
        "ml_blue": barrel_stock.blue_ml,
        "ml_dark": barrel_stock.dark_ml
    })

    plan = []

    if barrel_stock.red_ml >= 100:
        quantity = barrel_stock.red_ml // 100

        logger.info(f"Bottling {quantity} red potions")
        plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": quantity,
                }
        )
    if barrel_stock.green_ml >= 100:
        quantity = barrel_stock.green_ml // 100

        logger.info(f"Bottling {quantity} green potions")
        plan.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": quantity,
                }
        )

    if barrel_stock.blue_ml >= 100:
        quantity = barrel_stock.blue_ml // 100

        logger.info(f"Bottling {quantity} blue potions")
        plan.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": quantity,
                }
        )
    
    return plan
