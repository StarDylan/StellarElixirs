from fastapi import APIRouter
from src import database as db
import logging
import json

logger = logging.getLogger("catalog")

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    potions_to_sell = db.get_potions()[:20]
    
    catalog = []
    historical_record = []
    
    for potion_entry in potions_to_sell:
        if potion_entry.quantity == 0:
            continue # Don't include potions we don't have
        
        catalog.append({
            "sku": potion_entry.sku,
            "name": potion_entry.sku,
            "quantity": potion_entry.quantity,
            "price": potion_entry.price,
            "potion_type": potion_entry.potion_type.to_array(),
        })

        historical_record.append(db.PotionCatalogEntry(
            potion_entry.sku,
            potion_entry.price,
            potion_entry.quantity,
        ))

    
    if len(catalog) == 0:
        logger.info("No potions in inventory to list in catalog")
        return []


    db.add_historical_potion_catalog_data(historical_record)
    
    
    logger.info("Catalog with potions served", extra={
        "catalog": json.dumps(catalog)
    })
    
    return catalog
