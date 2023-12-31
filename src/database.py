from datetime import datetime, timezone
import os
import sqlalchemy
from sqlalchemy import create_engine, Connection
import typing as t
from src.models import Barrel
from src.constants import STARTING_GOLD
from src.models import BarrelDelta, BarrelStock, CartEntry, PotionEntry, PotionType

def database_connection_url():
    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)

def create_cart(conn: Connection, customer_name: str) -> int:
    """Create a new cart and return its id"""
    cart_id = conn.execute(
        sqlalchemy.text("""
            INSERT INTO carts (customer_name)
            VALUES (:customer_name)
            RETURNING id"""), 
            [{"customer_name": customer_name}]
    ).scalar_one()
    return cart_id

def set_item_in_cart(conn: Connection, cart_id: int, sku: int, quantity: int):
    """Add the specified number of potions to the cart"""
    conn.execute(
        sqlalchemy.text("""
            INSERT INTO cart_contents
            (cart_id, potion_id, price, quantity)
                    
            SELECT :cart_id, potion_types.id, potion_types.price, :quantity
            FROM potion_types
            WHERE potion_types.sku = :sku"""),
            [{"cart_id": cart_id, "sku": sku, "quantity": quantity}]
    )
       
def get_cart_contents(conn: Connection, cart_id: int) -> t.List[CartEntry]:
    """Return a list of all potions in the cart"""
    result = conn.execute(
        sqlalchemy.text("""
            SELECT a.potion_id, a.quantity, a.id, a.price
            FROM cart_contents a
            INNER JOIN (
                SELECT potion_id, MAX(id) id
                FROM cart_contents
                WHERE cart_id = :cart_id
                GROUP BY potion_id
            ) b ON a.potion_id = b.potion_id AND a.id = b.id"""),
            [{"cart_id": cart_id}]
    ).all()

        
    return [CartEntry(row.id, row.potion_id, row.quantity, row.price) for row in result]

def get_gold(conn: Connection):
    """Return the current amount of gold in the global inventory"""
    gold = conn.execute(
        sqlalchemy.text("""
            SELECT SUM(gold)
            FROM inventory_ledger""")
    ).scalar_one()

    return int(gold)
    
def add_gold(conn: Connection, gold_to_add: int, desc: str) -> int:
    """Add the specified amount of gold to the global inventory"""
    id = conn.execute(
        sqlalchemy.text("""INSERT INTO inventory_ledger
                        (gold, description)
                        VALUES (:gold, :description)
                        RETURNING id"""),
                        [{"gold": gold_to_add, "description": desc}]
    ).scalar_one()

    return id

def add_barrel_stock(conn: Connection, barrel_delta: BarrelDelta, desc: str) -> int:
    """Add the specified amount of each color to the global inventory
    
    Returns ledger line id"""
    id = conn.execute(
        sqlalchemy.text("""
            INSERT INTO inventory_ledger
            (red_ml, green_ml, blue_ml, dark_ml, description)
            VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml, :description)
            RETURNING id"""),
            [{"red_ml": barrel_delta.red_ml, 
                "green_ml": barrel_delta.green_ml, 
                "blue_ml": barrel_delta.blue_ml, 
                "dark_ml": barrel_delta.dark_ml, 
                "description": desc}]
    ).scalar_one()

    return id

def get_barrel_stock(conn: Connection) -> BarrelStock:
    """Return the current amount of each color in the global inventory"""
    result = conn.execute(
        sqlalchemy.text("SELECT SUM(red_ml) as red, \
                        SUM(green_ml) as green, \
                        SUM(blue_ml) as blue, \
                        SUM(dark_ml) as dark \
                        FROM inventory_ledger")
    ).one()
    return BarrelStock(int(result.red), int(result.green), 
                        int(result.blue), int(result.dark))

    
def add_potions_by_type(conn: Connection, potion_type: PotionType, quantity: int, desc: str):
    """Add the specified amount of potions of specific type to the inventory"""
        
    ledger_id = conn.execute(
        sqlalchemy.text(
            """INSERT INTO
                potion_ledger (qty_change, potion_id, description)
                (
                    SELECT :qty_change, potion_types.id, :desc
                    FROM potion_types
                    WHERE potion_types.red=:red AND
                    potion_types.green=:green AND
                    potion_types.blue=:blue AND 
                    potion_types.dark=:dark
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

def add_potions_by_id(conn: Connection, potion_id: int, quantity: int, desc: str):        
    ledger_id = conn.execute(
        sqlalchemy.text(
            """INSERT INTO
                potion_ledger (qty_change, potion_id, description)
                VALUES (:qty_change, :potion_id, :desc)
                RETURNING id"""),
        [{
            "qty_change": quantity,
            "potion_id": potion_id,
            "desc": desc
        }]).scalar_one()
    
    return ledger_id


def get_potion_type_by_sku(conn: Connection, sku: str) -> PotionType | None:
    """Return the potion id with the specified sku"""
    result = conn.execute(
        sqlalchemy.text("""
            SELECT red, green, blue, dark
            FROM potion_types
            WHERE sku = :sku""",
            [{"sku": sku}])
    ).first()

    if result is None:
        return None
    
    return PotionType(result.red, result.green, result.blue, result.dark)
    

def get_potions(conn: Connection) -> t.List[PotionEntry]:
    """Return a list of all potions in the inventory"""
    result = conn.execute(
        sqlalchemy.text("""
            SELECT
                potion_types.price,
                red,
                green,
                blue,
                dark,
                CAST(COALESCE( SUM(potion_ledger.qty_change), 0) AS INTEGER) AS qty,
                sku,
                potion_types.desired_qty
            FROM
                potion_types
            LEFT JOIN potion_ledger ON potion_ledger.potion_id = potion_types.id
            WHERE is_active = true
            GROUP BY
                potion_types.red,
                potion_types.green,
                potion_types.blue,
                potion_types.dark,
                potion_types.price,
                potion_types.sku,
                potion_types.desired_qty""")
    ).all()
    
    return [PotionEntry.from_db(row.red, row.green, row.blue, row.dark, 
                                row.qty, row.sku, row.price, row.desired_qty) 
                                for row in result]

def reset(conn: Connection):
    """Reset the game state. 
    All potions, barrels, and gold history are removed
    Gold starts at 100
    """
    conn.execute(
        sqlalchemy.text("DELETE FROM potion_ledger")
    )

    conn.execute(
        sqlalchemy.text("DELETE FROM inventory_ledger")
    )

    conn.execute(
        sqlalchemy.text("INSERT INTO inventory_ledger (gold, description) VALUES (:gold, :desc)"),
        [{"gold": STARTING_GOLD,
            "desc": "Starting Gold"}]
    )

def add_historical_catalog_data(conn: Connection, catalog: t.List[Barrel]):
    """Add the catalog data to the database"""
    current_time = datetime.now(tz=timezone.utc)
    for barrel in catalog:
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO wholesale_catalog_history
                (created_at, sku, ml_per_barrel, red, green, blue, dark, price, 
                    quantity)
                VALUES (:created_at, :sku, :ml_per_barrel, :red, :green, :blue, 
                    :dark, :price, :quantity)"""),
                [{  "created_at": current_time,
                    "sku": barrel.sku,
                    "ml_per_barrel": barrel.ml_per_barrel,
                    "red": barrel.potion_type[0],
                    "green": barrel.potion_type[1],
                    "blue": barrel.potion_type[2],
                    "dark": barrel.potion_type[3],
                    "price": barrel.price,
                    "quantity": barrel.quantity}]
        )

class PotionCatalogEntry(t.NamedTuple):
    sku: str
    price: int
    quantity: int

def add_historical_potion_catalog_data(conn: Connection, catalog: t.List[PotionCatalogEntry]):
    current_time = datetime.now(tz=timezone.utc)
    for entry in catalog:
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO potion_catalog_history
                (created_at, potion_id, price, quantity)
                        
                SELECT :created_at, potion_types.id, :price, :quantity
                FROM potion_types
                WHERE potion_types.sku = :sku"""),
                        [{  "sku": entry.sku,
                            "price": entry.price,
                            "quantity": entry.quantity,
                            "created_at": current_time}]
                )
class BottlePlanEntry(t.NamedTuple):
    potion_type: t.List[int]
    quantity: int

def add_bottling_history(conn: Connection, plan: t.List[BottlePlanEntry]):
    current_time = datetime.now(tz=timezone.utc)
    for entry in plan:
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO bottling_history
                (created_at, potion_id, quantity)
                        
                SELECT :created_at, potion_types.id, :quantity
                FROM potion_types
                WHERE potion_types.red = :red
                    AND potion_types.green = :green
                    AND potion_types.blue = :blue
                    AND potion_types.dark = :dark"""),
                        [{
                        "quantity": entry.quantity,
                        "created_at": current_time,
                        "red": entry.potion_type[0],
                        "green": entry.potion_type[1],
                        "blue": entry.potion_type[2],
                        "dark": entry.potion_type[3]}]
                )

def add_barrel_history(conn: Connection, plan: t.List[Barrel]):
    current_time = datetime.now(tz=timezone.utc)
    for entry in plan:
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO barrel_purchase_history
                (created_at, sku, quantity, red, green, blue, dark, ml_per_barrel, price)     
                VALUES (:created_at, :sku, :quantity, :red, :green, :blue, :dark, :ml_per_barrel, :price)
                """),
                        [{
                        "created_at": current_time,
                        "sku": entry.sku,
                        "quantity": entry.quantity,
                        "red": entry.potion_type[0],
                        "green": entry.potion_type[1],
                        "blue": entry.potion_type[2],
                        "dark": entry.potion_type[3],
                        "ml_per_barrel": entry.ml_per_barrel,
                        "price": entry.price}]
                )
            
def add_cart_checkout(conn: Connection, cart_id: int, payment: str):
    conn.execute(
        sqlalchemy.text("""
            INSERT INTO cart_checkouts
            (cart_id, payment)     
            VALUES (:cart_id, :payment)
            """),
                    [{
                    "cart_id": cart_id,
                    "payment": payment}]
            )

class CartLineItem(t.NamedTuple):
    line_item_id: int
    item_sku: str
    customer_name: str
    line_item_total: int
    timestamp: str

def get_cart_line_items(conn: Connection, offset: int, limit: int, sort_col: str, sort_order: str, name: str, sku: str) -> t.Tuple[t.List[CartLineItem], int]:
    order_by_append = f"{str(sort_col)} {str(sort_order)}"

    name_where = ""
    if name != "":
        name_where = f"AND carts.customer_name ILIKE '%{name}%'"

    sku_where = ""
    if sku != "":
        sku_where = f"AND potion_types.sku ILIKE '%{sku}%'"

    result = conn.execute(
        sqlalchemy.text(f"""
            SELECT cart_contents.created_at AS timestamp, cart_contents.id AS line_item_id,
                            quantity * cart_contents.price AS line_item_total, carts.customer_name, 
                        potion_types.sku AS item_sku,
                        COUNT(*) OVER() AS full_count
            FROM cart_contents
            JOIN carts ON carts.id = cart_contents.cart_id
            JOIN potion_types ON potion_types.id = cart_contents.potion_id
            WHERE true {name_where} {sku_where}
            ORDER BY {order_by_append}
            LIMIT :limit
            OFFSET :offset
            """),
            [{
                "limit": limit,
                "offset": offset
            }]
    ).all()

    if len(result) == 0:
        return ([], 0)

    return ([CartLineItem(row.line_item_id, row.item_sku, row.customer_name, row.line_item_total, row.timestamp) for row in result], result[0].full_count)
