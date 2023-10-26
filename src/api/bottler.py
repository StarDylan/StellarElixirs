from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.logic.bottle_logic import bottle_planner
from src.models import BarrelDelta, PotionType
import logging
import json

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

    with db.engine.begin() as conn:
        bottle_plan_history_record = [db.BottlePlanEntry(bottle.potion_type, bottle.quantity) for bottle in potions_delivered]
        db.add_bottling_history(conn, bottle_plan_history_record)

        barrel_delta = BarrelDelta.init_zero()
        
        for delivered_potion in potions_delivered:
            db.add_potions_by_type(
                conn,
                PotionType.from_array(delivered_potion.potion_type), 
                delivered_potion.quantity,
                "Bottle Delivery")

            barrel_delta.remove_stock(PotionType.from_array(delivered_potion.potion_type), 
                                    delivered_potion.quantity)

        db.add_barrel_stock(conn, barrel_delta, "Bottle Delivery")

        logger.info("Received Bottles", extra={
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

    with db.engine.begin() as conn:
        barrel_stock = db.get_barrel_stock(conn)
        potions = db.get_potions(conn)


        plan = bottle_planner(barrel_stock, potions)


        final_bottle_plan = []
        for bottle in plan:
            final_bottle_plan.append(
                {
                    "potion_type": bottle.potion_type.to_array(),
                    "quantity": bottle.quantity,
                }
            )

        if len(final_bottle_plan) == 0:
            logger.info("Not bottling")
        else:
            logger.info("Planned Bottles", extra={
                "barrel_stock": json.dumps(barrel_stock, default=vars),
                "bottle_plan": json.dumps(final_bottle_plan, default=vars),
            })

    
        return final_bottle_plan
