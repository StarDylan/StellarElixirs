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
    new_cart_id = db.create_cart(new_cart.customer)
        
    print(f"Creating cart {new_cart_id}")
    return {"cart_id": new_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {"error":"Not Implemented"}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print(f"Set item quantity of {item_sku} to {cart_item.quantity} in cart {cart_id}")

    
    potion_id = db.get_potion_by_sku(item_sku).id

    if potion_id is None:
        return f"Error: SKU '{item_sku}' not found"

    db.set_item_in_cart(cart_id, potion_id, cart_item.quantity)

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(f"Checkout cart #{cart_id}, Payment: {cart_checkout}")


    cart_contents = db.get_cart_contents(cart_id)

    total_price = 0
    total_potions = 0

    # Remove Specified Potions from Inventory
    for cart_entry in cart_contents:
        new_entry = db.add_potions_by_id(cart_entry.potion_id, -cart_entry.quantity)

        total_price += new_entry.price * cart_entry.quantity
        total_potions += cart_entry.quantity

    # Add Gold Gold
    db.add_gold(total_price)
    
    # Delete Cart and Contents
    db.delete_cart(cart_id)

    print(f"Cart #{cart_id} has been checked out with {total_potions} potions")

    return {"total_potions_bought": total_potions, "total_gold_paid": total_price}
