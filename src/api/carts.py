from enum import Enum
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


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    offset = 0
    limit = 5
    if search_page != "":
        offset = int(search_page)

    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    results, total = db.get_cart_line_items(offset, limit, sort_col.value, sort_order.value, customer_name, potion_sku)
    next = ""
    if total - offset > limit:
        next = str(offset + limit)

    previous = ""
    if offset > 0:
        previous = str(offset - limit)

    items = []
    for item in results:
        items.append(
            {
                "line_item_id": item.line_item_id,
                "item_sku": item.item_sku,
                "customer_name": item.customer_name,
                "line_item_total": item.line_item_total,
                "timestamp": item.timestamp,
            }
        )

    return {
        "previous": previous,
        "next": next,
        "results": items,
    }



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
        db.add_potions_by_id(
            cart_entry.potion_id,
            -cart_entry.quantity,
            f"Checkout for Cart #{cart_id}"
        )
        total_price += cart_entry.price * cart_entry.quantity
        total_potions += cart_entry.quantity

    # Add Gold
    db.add_gold(total_price, f"Checkout for Cart #{cart_id}")
    
    logger.info(f"Cart #{cart_id} has been checked out", extra={  # noqa: E501
        "cart_id": cart_id,
        "payment": cart_checkout.payment,
        "total_potions_bought": total_potions,
        "total_gold_paid": total_price
    })

    db.add_cart_checkout(cart_id, cart_checkout.payment)

    return {"total_potions_bought": total_potions, "total_gold_paid": total_price}
