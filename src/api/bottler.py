from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.models import BarrelDelta, BarrelStock, PotionType

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

    print("Barrels Recieved!")

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

    plan = []

    if barrel_stock.red_ml >= 100:
        plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": barrel_stock.red_ml // 100,
                }
        )
    if barrel_stock.green_ml >= 100:
        plan.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": barrel_stock.green_ml // 100,
                }
        )

    if barrel_stock.blue_ml >= 100:
        plan.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": barrel_stock.blue_ml // 100,
                }
        )
    
    return plan
