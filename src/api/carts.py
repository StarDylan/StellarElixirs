from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
import logging

logger = logging.getLogger("carts")

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
        
    logger.info(f"Creating cart {new_cart_id}", extra={
        "cart_id": new_cart_id
    })

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

    db.set_item_in_cart(cart_id, item_sku, cart_item.quantity)

    logger.info(f"Set {item_sku} to {cart_item.quantity} in #{cart_id}",
        extra={
            "cart_id": cart_id,
            "item_sku": item_sku,
            "quantity": cart_item.quantity,
        }
    )

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    cart_contents = db.get_cart_contents(cart_id)

    total_price = 0
    total_potions = 0

    # Remove Specified Potions from Inventory
    for cart_entry in cart_contents:
        potion_entry = db.add_potions_by_id(cart_entry.potion_id, -cart_entry.quantity, 
                                            f"Checkout for Cart #{cart_id}")

        total_price += cart_entry.price * cart_entry.quantity
        total_potions += cart_entry.quantity

    # Add Gold
    db.add_gold(total_price, "Checkout for Cart #{cart_id")
    
    logger.info(f"Cart #{cart_id} has been checked out", extra={  # noqa: E501
        "cart_id": cart_id,
        "payment": cart_checkout.payment,
        "total_potions_bought": total_potions,
        "total_gold_paid": total_price
    })

    db.add_cart_checkout(cart_id, cart_checkout.payment)

    return {"total_potions_bought": total_potions, "total_gold_paid": total_price}
