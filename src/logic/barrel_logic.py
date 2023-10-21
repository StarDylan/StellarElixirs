from src.models import BARREL_TYPES, Barrel, BarrelStock
from typing import Callable
import copy


### Helper functions ###
def price(barrel: Barrel) -> int:
    '''Returns the price of 1 barrel, given a barrel object.'''
    return barrel.price

def ml_to_gold_ratio(barrel: Barrel) -> float:
    '''Returns the ml to gold ratio, such that a higher ratio indicates more ml per gold.'''
    return barrel.ml_per_barrel / barrel.price

def type_must_be(barrel_type: list[int]) -> Callable[[Barrel], bool]:
    '''Returns true if the barrel is the given color.'''
    def filter_by_color(barrel: Barrel) -> bool:
        return barrel.potion_type == barrel_type
    
    return filter_by_color


####### Rule Theory #######

# TickNum = (Hour - 1) / 2
#
####### Small Catalogs are presented after 8th tick of Thurs 


def buy_one_barrel(barrel: Barrel, plan: list[Barrel], catalog: list[Barrel]):
    '''Modifies the plan to include one more barrel of the given type.
    And removes one qty from the passed in Barrel Object.
    Removes it from catalog if it's the last one.'''

    copy_barrel = copy.deepcopy(barrel)

    # Find the barrel we want to buy
    existing_barrel = next(filter(lambda a: a.sku == barrel.sku, plan), None)

    if existing_barrel is None:
        # If it doesn't exist, add it
        copy_barrel.quantity = 1
        plan.append(copy_barrel)
    else:
        # If it does exist, increment the quantity
        existing_barrel.quantity += 1

    
    # Update Original Barrel
    barrel.quantity -= 1

    # Remove from catalog if it's the last one
    if barrel.quantity == 0:
        catalog.remove(barrel)


def barrel_planner(gold: int, barrel_stock: BarrelStock, catalog: list[Barrel]) -> list[Barrel]:
    '''Logic for buying barrels, given a budget, current barrel stock, and a catalog of barrels to buy from.
    
    Goals: Most spread of barrels possible to capture the most customers.'''
    catalog = copy.deepcopy(catalog)
    barrel_stock = copy.copy(barrel_stock)
    budget = gold

    barrels_to_buy = []

    

    while True:
        # If we buy/skip every barrel, break
        if len(catalog) == 0:
            break

        # If we can't afford cheapest barrel, break
        if min(catalog, key=price).price > budget:
            break

        ### OTHER CONDIITONS TO BREAK (BALKING) ###

        for potion_type in BARREL_TYPES:
            
            # Find best value barrel for potion type
            best_value_barrel = max(filter(type_must_be(potion_type),catalog), key=ml_to_gold_ratio, default=None)

            if best_value_barrel is None:
                # If we can't find a barrel of this type, skip it
                continue

            # See if we can afford it
            if best_value_barrel.price > budget:
                # Since we can't afford one of these, we can't afford any of them
                catalog.remove(best_value_barrel)
                continue
                
            # Yay we can afford it, so let's buy one
            buy_one_barrel(best_value_barrel, barrels_to_buy, catalog)
            budget -= best_value_barrel.price

    return list(barrels_to_buy)