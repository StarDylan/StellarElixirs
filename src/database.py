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
        gold = connection.execute(
            sqlalchemy.text("SELECT SUM(gold)\
                            FROM inventory_ledger")
        ).scalar_one()

        return int(gold)
    
def add_gold(gold_to_add: int, desc: str) -> int:
    """Add the specified amount of gold to the global inventory"""
    with engine.begin() as connection:
        id = connection.execute(
            sqlalchemy.text("""INSERT INTO inventory_ledger
                            (gold, description)
                            VALUES (:gold, :description)
                            RETURNING id"""),
                            [{"gold": gold_to_add, "description": desc}]
        ).scalar_one()

        return id

def add_barrel_stock(barrel_delta: BarrelDelta, desc: str) -> int:
    """Add the specified amount of each color to the global inventory
    
    Returns ledger line id"""
    with engine.begin() as connection:
        id = connection.execute(
            sqlalchemy.text("INSERT INTO inventory_ledger \
                            (red_ml, green_ml, blue_ml, dark_ml, description) \
                            VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml, \
                                :description)"),
                            [{"red_ml": barrel_delta.red_ml, 
                              "green_ml": barrel_delta.green_ml, 
                              "blue_ml": barrel_delta.blue_ml, 
                              "dark_ml": barrel_delta.dark_ml, 
                              "description": desc}]
        ).scalar_one()

    return id

def get_barrel_stock() -> BarrelStock:
    """Return the current amount of each color in the global inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT SUM(red_ml) as red, \
                            SUM(green_ml) as green, \
                            SUM(blue_ml) as blue, \
                            SUM(dark_ml) as dark \
                            FROM inventory_ledger")
        ).one()
        return BarrelStock(int(result.red), int(result.green), 
                           int(result.blue), int(result.dark))

    
def add_potion_by_type(potion_type: PotionType, quantity: int, desc: str):
    """Add the specified amount of potions of specific type to the inventory"""

    with engine.begin() as connection:
        
        ledger_id = connection.execute(
            sqlalchemy.text(
                """INSERT INTO
                    potion_ledger (qty_change, potion_id, description)
                    (
                        SELECT :qty_change, potion_inventory.id, :desc
                        FROM potion_inventory
                        WHERE potion_inventory.red=:red AND
                        potion_inventory.green=:green AND
                        potion_inventory.blue=:blue AND 
                        potion_inventory.dark=:dark
                    )
                    RETURNING id"""),
            [{
                "qty_change": quantity,
                "red": potion_type.red,
                "green": potion_type.green,
                "blue": potion_type.blue,
                "dark": potion_type.dark,
                "desc": desc
            }]).scalar_one()
    return ledger_id
        

def add_potions_by_id(potion_id: int, quantity: int, desc: str) -> PotionEntry:
    """Add the specified amount of potions to the inventory.
    Potion must already exist."""
    with engine.begin() as connection:
            id_added = connection.execute(
                sqlalchemy.text("""
                    INSERT INTO potion_ledger (qty_change, potion_id, description)
                    VALUES (:qty_change, :potion_id, :desc)
                    RETURNING id
                    """),
                [{
                    "qty_change": quantity,
                    "potion_id": potion_id,
                    "desc": desc
                }]
            ).scalar_one()

            return id_added


def get_potion_by_sku(sku: str) -> PotionEntry | None:
    """Return the potion id with the specified sku"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(f"SELECT id, red, green, blue, dark, \
                            quantity, sku, price, desired_qty \
                            FROM potion_inventory \
                            WHERE sku = \'{sku}\'")
        ).first()
        if result is None:
            return None
        return PotionEntry.from_db(result.id, result.red, result.green, 
                                    result.blue, result.dark, result.quantity, 
                                    result.desired_qty, result.sku, result.price)
    
def get_potion_by_id(id: int) -> PotionEntry | None:
    """Return the potion with the specified id"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(f"SELECT id, red, green, blue, dark, \
                            desired_qty, quantity, sku, price \
                            FROM potion_inventory \
                            WHERE id = {id}")
        ).first()
        if result is None:
            return None
        return PotionEntry.from_db(result.id, result.red, result.green, 
                                    result.blue, result.dark, result.quantity,
                                    result.desired_qty, result.sku, result.price)
    
    

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