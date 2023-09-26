from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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

    red = 0
    gold_used = 0
    for barrel in barrels_delivered:
        red += barrel.ml_per_barrel * barrel.quantity

        gold_used += barrel.price * barrel.quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT num_red_ml, gold FROM global_inventory"))
        result = result.one()
        num_red_ml_existing =  result[0]
        gold = result[1]

        print("Barrels Recieved!")
        print(f"Red ML go from {num_red_ml_existing} to {num_red_ml_existing + red}")
        print(f"Gold go from {gold} to {gold - gold_used}")

        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET num_red_ml={num_red_ml_existing + red}"))
        
        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET gold={gold - gold_used}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT num_red_potions, gold FROM global_inventory"))
        result = result.one()
        num_red_potions = result[0]
        gold = result[1]

        print("Wholesale Catalog Recieved!")
        print(f"num_red_potions: {num_red_potions}; Gold: {gold}")
        if num_red_potions < 10 and gold >= 100:
            print("Buy SMALL_RED_BARREL")
            return [
                {
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                }
            ]
        
           
        else:
            print("Buy Nothing")
            return []
