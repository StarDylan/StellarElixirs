from fastapi import APIRouter, Depends
from src.api import auth
from src import database as db
import logging

logger = logging.getLogger("admin")

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

    logger.info("Resetting Shop State")

    db.reset()


@router.get("/shop_info/")
def get_shop_info():
    """ """

    logger.info("Someone getting Shop Info")

    return {
        "shop_name": "Stellar Elixirs",
        "shop_owner": "Dylan Starink",
    }

