from fastapi import APIRouter, Depends
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    db.reset()


@router.get("/shop_info/")
def get_shop_info():
    """ """
    return {
        "shop_name": "Stellar Elixirs",
        "shop_owner": "Dylan Starink",
    }

