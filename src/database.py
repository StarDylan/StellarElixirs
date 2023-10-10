import os
import sqlalchemy
from sqlalchemy import create_engine
import typing as t

from src.constants import STARTING_GOLD
from src.models import BarrelDelta, BarrelStock, CartEntry, PotionEntry, PotionType

def database_connection_url():
    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)


def create_cart(customer_name: str) -> int:
    """Create a new cart and return its id"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(f"INSERT INTO carts (customer_name) \
                            VALUES (\'{customer_name}\') \
                            RETURNING id")
        ).one()
        return result[0]
    
def set_item_in_cart(cart_id: int, potion_id: int, quantity: int):
    """Add the specified number of potions to the cart"""
    with engine.begin() as connection:
        existing_quantity_or_none = connection.execute(
            sqlalchemy.text(f"SELECT quantity \
                                FROM cart_contents \
                                WHERE potion_id = {potion_id} AND \
                                cart_id = {cart_id}")).first()
        
        if existing_quantity_or_none is None:

            connection.execute(
                sqlalchemy.text(f"INSERT INTO cart_contents \
                                (cart_id, potion_id, quantity) \
                                VALUES ({cart_id}, {potion_id}, {quantity})")
            )
        else:
            connection.execute(
                sqlalchemy.text(f"UPDATE cart_contents \
                                SET quantity = {quantity} \
                                WHERE potion_id = {potion_id} \
                                AND cart_id = {cart_id}"))

def get_cart_contents(cart_id: int) -> t.List[CartEntry]:
    """Return a list of all potions in the cart"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(f"SELECT potion_id, quantity \
                                FROM cart_contents \
                                WHERE cart_id = {cart_id}")
        ).all()

        
        return [CartEntry(row.potion_id, row.quantity) for row in result]

def delete_cart(cart_id: int):
    """Delete the specified cart and associated contents"""
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(f"DELETE FROM carts WHERE id={cart_id}")
        )

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

def add_barrel_stock(barrel_delta: BarrelDelta):
    """Add the specified amount of each color to the global inventory"""
    with engine.begin() as connection:
        connection.execute(
           sqlalchemy.text( f"UPDATE global_inventory \
                            SET num_red_ml = num_red_ml + {barrel_delta.red_ml}, \
                                num_green_ml = num_green_ml + {barrel_delta.green_ml}, \
                                num_blue_ml = num_blue_ml + {barrel_delta.blue_ml}, \
                                num_dark_ml = num_dark_ml + {barrel_delta.dark_ml}")
        )

def get_barrel_stock() -> BarrelStock:
    """Return the current amount of each color in the global inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml \
                                FROM global_inventory")
        ).one()
        return BarrelStock(result.num_red_ml, result.num_green_ml, 
                           result.num_blue_ml, result.num_dark_ml)

    
def add_potions_by_type(potion_type: PotionType, quantity: int):
    """Add the specified amount of potions of specific type to the inventory"""

    price = 50

    if potion_type.red + potion_type.green + potion_type.blue + potion_type.dark != 100:
        raise ValueError(f"Potion components must add up to 100 \
                            \n(red = {potion_type.red}, \
                            green = {potion_type.green}, \
                            blue = {potion_type.blue}, \
                            dark = {potion_type.dark}) \
                            @ quantity = {quantity}")

    with engine.begin() as connection:
        
        existing_potion_amount_or_none = connection.execute(
            sqlalchemy.text(f"SELECT quantity \
                                FROM potion_inventory \
                                WHERE red = {potion_type.red} \
                                AND green = {potion_type.green} \
                                AND blue = {potion_type.blue} \
                                AND dark = {potion_type.dark}")).first()

        if existing_potion_amount_or_none is None:

            sku = f"R{potion_type.red}_G{potion_type.green}" + \
                f"_B{potion_type.blue}_D{potion_type.dark}"
            
            connection.execute(
                sqlalchemy.text(f"INSERT INTO potion_inventory \
                                (sku, red, green, blue, dark, quantity, price) \
                                VALUES (\'{sku}\', {potion_type.red}, {potion_type.green}, {potion_type.blue}, {potion_type.dark}, {quantity}, {price})")  # noqa: E501
            )
        else:
            connection.execute(
                sqlalchemy.text(f"UPDATE potion_inventory \
                                SET quantity = quantity + {quantity} \
                                WHERE red={potion_type.red} \
                                AND green={potion_type.green} \
                                AND blue={potion_type.blue} \
                                AND dark={potion_type.dark}"
                                )
            )

def add_potions_by_id(potion_id: int, quantity: int) -> PotionEntry:
    """Add the specified amount of potions to the inventory.
    Potion must already exist."""
    with engine.begin() as connection:
            results = connection.execute(
                sqlalchemy.text(f"UPDATE potion_inventory \
                                SET quantity = quantity + {quantity} \
                                WHERE id={potion_id} \
                                RETURNING id, red, green, blue, dark, quantity, sku, price"  # noqa: E501
                                )
            ).first()

            return PotionEntry.from_db(results.id, results.red, results.green, 
                                       results.blue, results.dark, results.quantity, 
                                       results.sku, results.price)


def get_potion_by_sku(sku: str) -> PotionEntry | None:
    """Return the potion id with the specified sku"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(f"SELECT id, red, green, blue, dark, quantity, sku, price \
                                FROM potion_inventory \
                                WHERE sku = \'{sku}\'")
        ).first()
        if result is None:
            return None
        return PotionEntry.from_db(result.id, result.red, result.green, 
                                    result.blue, result.dark, result.quantity, 
                                    result.sku, result.price)
    
def get_potion_by_id(id: int) -> PotionEntry | None:
    """Return the potion with the specified id"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(f"SELECT id, red, green, blue, dark, quantity, sku, price \
                                FROM potion_inventory \
                                WHERE id = {id}")
        ).first()
        if result is None:
            return None
        return PotionEntry.from_db(result.id, result.red, result.green, 
                                    result.blue, result.dark, result.quantity, 
                                    result.sku, result.price)
    
    

def get_potions() -> t.List[PotionEntry]:
    """Return a list of all potions in the inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT id, red, green, blue, dark, \
                            quantity, desired_qty, sku, price \
                                FROM potion_inventory")
        ).all()
        
        return [PotionEntry.from_db(row.id, row.red, row.green, row.blue, row.dark, 
                                    row.quantity,row.desired_qty, row.sku, row.price) 
                                    for row in result]
    
def reset():
    """Reset the game state. 
    Gold goes to 100, All potions are removed,
    All barrels are removed, Carts are all reset."""
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(f"UPDATE global_inventory SET gold = {STARTING_GOLD}")
        )

        connection.execute(
            sqlalchemy.text("DELETE FROM carts")
        )

        connection.execute(
            sqlalchemy.text("DELETE FROM potion_inventory")
        )