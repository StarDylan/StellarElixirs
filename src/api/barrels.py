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

    with db.engine.begin() as conn:
        db.add_historical_catalog_data(conn, wholesale_catalog)
        
        gold = db.get_gold(conn)

        barrel_stock = db.get_barrel_stock(conn)
        potion_stock = db.get_potions(conn)

        now = datetime.now(tz=pytz.timezone("America/Los_Angeles"))
        
        day_of_week = now.weekday()
        tick =int(( now.hour - 1 ) / 2)
        
        plan = barrel_planner(day_of_week, tick, gold, barrel_stock, wholesale_catalog, potion_stock)
        db.add_barrel_history(conn, plan)

        # Calculate total price
        total_price = sum([barrel.price * barrel.quantity for barrel in plan])
        total_barrels = sum([barrel.quantity for barrel in plan])


        logger.info("Finished Barrel Planning", extra={
            "gold": gold,
            "gold_paid": total_price,
            "buying_barrels": total_barrels,
            "barrel_stock": json.dumps(barrel_stock, default=vars),
            "catalog": json.dumps(wholesale_catalog, default=vars),
        })

        barrels_to_buy = []
        for barrel in plan:
            barrels_to_buy.append({
                "sku": barrel.sku,
                "quantity": barrel.quantity,
            })      

    return barrels_to_buy