import os
import dotenv
import sqlalchemy
from sqlalchemy import create_engine
import typing as t

from src.constants import STARTING_GOLD
from src.models import BarrelStock, PotionEntry

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)


def get_gold():
    """Return the current amount of gold in the global inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT gold FROM global_inventory")
        ).one()
        return result[0]
    
def add_gold(gold_to_add: int):
    """Add the specified amount of gold to the global inventory"""
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(f"UPDATE global_inventory SET gold=gold + {gold_to_add}")
        )

def add_barrel_stock(new_barrels: BarrelStock):
    """Add the specified amount of each color to the global inventory"""
    with engine.begin() as connection:
        connection.execute(
           sqlalchemy.text( f"UPDATE global_inventory \
                            SET num_red_ml=num_red_ml + {new_barrels.red_ml} \
                            SET num_green_ml=num_green_ml + {new_barrels.green_ml} \
                            SET num_blue_ml=num_blue_ml + {new_barrels.blue_ml} \
                            SET num_dark_ml=num_dark_ml + {new_barrels.dark_ml}")
        )

def get_barrel_stock():
    """Return the current amount of each color in the global inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml \
                                FROM global_inventory")
        ).one()
        return BarrelStock(*result)

    
def add_potions(quantity: int, red: int, green: int, blue: int, dark: int):
    """Add the specified amount of potions of specific type to the inventory"""

    if red + green + blue + dark != 100:
        raise ValueError(f"Potion components must add up to 100 \
                            \n(red={red}, green={green}, blue={blue}, dark={dark}) \
                            @ quantity={quantity}")

    with engine.begin() as connection:
        
        existing_potion_amount_or_none = connection.execute(
            sqlalchemy.text(f"SELECT quantity \
                                FROM potion_inventory \
                                WHERE red={red} AND green={green} \
                                AND blue={blue} AND dark={dark}")).first()

        if existing_potion_amount_or_none is None:
            connection.execute(
                sqlalchemy.text(f"INSERT INTO potion_inventory \
                                (red, green, blue, dark, quantity) \
                                VALUES ({red}, {green}, {blue}, {dark}, {quantity})")
            )
        else:
            connection.execute(
                sqlalchemy.text(f"UPDATE potion_inventory \
                                SET quantity=quantity + {quantity} \
                                WHERE red={red} AND green={green} \
                                AND blue={blue} AND dark={dark}")
            )
def get_potions() -> t.List[PotionEntry]:
    """Return a list of all potions in the inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT red, green, blue, dark, quantity \
                                FROM potion_inventory")
        ).all()
        
        return [PotionEntry(*row) for row in result]
    
def reset():
    """Reset the game state. 
    Gold goes to 100, All potions are removed,
    All barrels are removed, Carts are all reset."""
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(f"UPDATE global_inventory SET gold={STARTING_GOLD}")
        )

        connection.execute(
            sqlalchemy.text("DELETE FROM carts")
        )

        connection.execute(
            sqlalchemy.text("DELETE FROM potion_inventory")
        )