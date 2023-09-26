from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
    

    red = 0
    for potion in potions_delivered:
        red += potion.quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT num_red_potions, num_red_ml FROM global_inventory"))
        result = result.one()
        existing_red =  result[0]
        existing_ml = result[1]

        red_ml_used = 0
        for bottle in potions_delivered:
            red_ml_used += bottle.quantity * bottle.potion_type[0]

        print("Barrels Recieved!")
        print(f"Red potions go from {existing_red} to {existing_red + red}")
        print(f"Red ML go from {existing_ml} to {existing_ml - red_ml_used}")

        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET num_red_potions={existing_red + red}"))
        
        
        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET num_red_ml={existing_ml - red_ml_used}"))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT (num_red_ml) FROM global_inventory"))
        num_red_ml = result.one()[0]

        print("Bottler Plan!")
        print(f"Red ML: {num_red_ml}")

        if num_red_ml >= 100:

            # Each bottle has a quantity of what proportion of red, blue, and
            # green potion to add.
            # Expressed in integers from 1 to 100 that must sum up to 100.

            # Initial logic: bottle all barrels into red potions.

            print(f"Number of Bottled potions = {num_red_ml // 100}")
            return [
                    {
                        "potion_type": [100, 0, 0, 0],
                        "quantity": num_red_ml // 100,
                    }
                ]
        else:
            print("No Bottling!")
            return []
