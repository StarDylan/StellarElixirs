from fastapi import APIRouter, Depends
from src.api import auth
from src import database as db
from src.logic.barrel_logic import barrel_planner
from src.models import Barrel, BarrelDelta
from datetime import datetime
import logging
import pytz
import json

logger = logging.getLogger("barrels")

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """

    barrel_delta = BarrelDelta.init_zero()
    gold_paid = 0

    for barrel in barrels_delivered:
        barrel_delta.add_stock(barrel.potion_type,barrel.ml_per_barrel, barrel.quantity)

        gold_paid += barrel.price * barrel.quantity

    with db.engine.begin() as conn:
        db.add_gold(conn, -gold_paid, "Barrel Delivery")
        db.add_barrel_stock(conn, barrel_delta, "Barrel Delivery")

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

    barrels_to_buy = []

    return barrels_to_buy