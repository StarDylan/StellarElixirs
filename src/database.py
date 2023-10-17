import os
import sqlalchemy
from sqlalchemy import create_engine
import typing as t
from src.api.barrels import Barrel

from src.constants import STARTING_GOLD
from src.models import BarrelDelta, BarrelStock, CartEntry, PotionEntry, PotionType

def database_connection_url():
    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)

def create_cart(customer_name: str) -> int:
    """Create a new cart and return its id"""
    with engine.begin() as connection:
        cart_id = connection.execute(
            sqlalchemy.text("""
                INSERT INTO carts (customer_name)
                VALUES (:customer_name)
                RETURNING id"""), 
                [{"customer_name": customer_name}]
        ).scalar_one()
        return cart_id

def set_item_in_cart(cart_id: int, potion_id: int, quantity: int):
    """Add the specified number of potions to the cart"""
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""
                INSERT INTO cart_contents
                (cart_id, potion_id, quantity)
                VALUES (:cart_id, :potion_id, :quantity)"""),
                [{"cart_id": cart_id, "potion_id": potion_id, "quantity": quantity}]
        )
       
def get_cart_contents(cart_id: int) -> t.List[CartEntry]:
    """Return a list of all potions in the cart"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT a.potion_id, a.quantity, a.id
                FROM cart_contents a
                INNER JOIN (
                    SELECT potion_id, MAX(id) id
                    FROM cart_contents
                    WHERE cart_id = :cart_id
                    GROUP BY potion_id
                ) b ON a.potion_id = b.potion_id AND a.id = b.id"""),
                [{"cart_id": cart_id}]
        ).all()

        
        return [CartEntry(row.id, row.potion_id, row.quantity) for row in result]

def get_gold():
    """Return the current amount of gold in the global inventory"""
    with engine.begin() as connection:
        gold = connection.execute(
            sqlalchemy.text("""
                SELECT SUM(gold)
                FROM inventory_ledger""")
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
            sqlalchemy.text("""
                INSERT INTO inventory_ledger
                (red_ml, green_ml, blue_ml, dark_ml, description)
                VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml, :description)"""),
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

    
def add_potions_by_type(potion_type: PotionType, quantity: int, desc: str):
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
        

def add_potions_by_id(potion_id: int, quantity: int, desc: str) -> int:
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


def get_potion_type_by_sku(sku: str) -> PotionType | None:
    """Return the potion id with the specified sku"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT id, red, green, blue, dark
                FROM potion_inventory
                WHERE sku = :sku""",
                [{"sku": sku}])
        ).first()

        if result is None:
            return None
        
        return PotionType(result.id, result.red, result.green, result.blue, result.dark)


def get_potion_type_by_id(id: int) -> PotionType | None:
    """Return the potion with the specified id"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT id, red, green, blue, dark
                FROM potion_inventory
                WHERE id = :id"""),
                [{"id": id}]
        ).first()
        if result is None:
            return None
        
        return PotionType(result.id, result.red, result.green, result.blue, result.dark)
    
    

def get_potions() -> t.List[PotionEntry]:
    """Return a list of all potions in the inventory"""
    with engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT
                    potion_inventory.id,
                    red,
                    green,
                    blue,
                    dark,
                    COALESCE( SUM(potion_ledger.qty_change), 0) AS qty,
                    sku
                FROM
                    potion_inventory
                LEFT JOIN potion_ledger ON potion_ledger.potion_id = potion_inventory.id
                GROUP BY
                    potion_inventory.id,
                    potion_inventory.red,
                    potion_inventory.green,
                    potion_inventory.blue,
                    potion_inventory.dark""")
        ).all()
        
        return [PotionEntry.from_db(row.id, row.red, row.green, row.blue, row.dark, 
                                    int(row.qty), row.sku) 
                                    for row in result]

def reset():
    """Reset the game state. 
    All potions, barrels, and gold history are removed
    Gold starts at 100
    """
    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("DELETE FROM potion_ledger")
        )

        connection.execute(
            sqlalchemy.text("DELETE FROM inventory_ledger")
        )

        connection.execute(
            sqlalchemy.text("INSERT INTO inventory_ledger (gold) VALUES (:gold)"),
            [{"gold": STARTING_GOLD}]
        )

def add_historical_catalog_data(catalog: t.List[Barrel]):
    """Add the catalog data to the database"""
    with engine.begin() as connection:
        for barrel in catalog:
            connection.execute(
                sqlalchemy.text("""
                    INSERT INTO wholesale_catalog_history
                    (sku, ml_per_barrel, red, green, blue, dark, price, quantity)
                    VALUES (:sku, :ml_per_barrel, :red, :green, :blue, :dark, :price, :quantity)"""),
                    [{  "sku": barrel.sku,
                        "ml_per_barrel": barrel.ml_per_barrel,
                        "red": barrel.potion_type.red,
                        "green": barrel.potion_type.green,
                        "blue": barrel.potion_type.blue,
                        "dark": barrel.potion_type.dark,
                        "price": barrel.price,
                        "quantity": barrel.quantity}]
            )
