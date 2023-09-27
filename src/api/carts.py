from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
import sqlalchemy

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT MAX(id) FROM carts")).one()
        if not result[0]:
            new_cart_id = 1
        else:
            new_cart_id = result[0] + 1

        result = connection.execute(sqlalchemy.text(
            f"INSERT INTO carts (id, num_red_potions) \
            VALUES ({new_cart_id}, 0)"))
        
    print(f"Creating cart {new_cart_id}")
    return {"cart_id": new_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print(f"Set item quantity of {item_sku} to {cart_item.quantity} in cart {cart_id}")

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            f"UPDATE carts SET num_red_potions={cart_item.quantity} \
                WHERE id={cart_id}"))
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(f"Checkout cart #{cart_id}, Payment: {cart_checkout}")

    with db.engine.begin() as connection:
        red_potions = connection.execute(sqlalchemy.text(
            f"SELECT (num_red_potions) FROM carts \
                WHERE id={cart_id}")).one()[0]
        
        
        red_potions = connection.execute(sqlalchemy.text(
            f"SELECT (num_red_potions) FROM carts \
                WHERE id={cart_id}")).one()[0]
        
        num_red_potions_existing = connection.execute(sqlalchemy.text(
            "SELECT num_red_potions FROM global_inventory")).one()[0]

        
        gold_existing = connection.execute(sqlalchemy.text(
            "SELECT gold FROM global_inventory")).one()[0]
        
        # Set Potions
        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET \
            num_red_potions={num_red_potions_existing - red_potions}"))
        
        # Set Gold
        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET \
            gold={gold_existing + (red_potions * 50)}"))
        
        connection.execute(sqlalchemy.text(
            f"DELETE FROM carts WHERE id={cart_id}"))

        print(f"Cart #{cart_id} has been checked out with {red_potions} red potions")

    return {"total_potions_bought": red_potions, "total_gold_paid": red_potions * 50}
