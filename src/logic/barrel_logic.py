from dataclasses import dataclass
from enum import Enum
from src.models import BARREL_TYPES, Barrel, BarrelDelta, BarrelStock, PotionEntry
from typing import Callable
import copy
import logging

logger = logging.getLogger("admin")

class CatalogType(Enum):
    LARGE = 1
    MEDIUM = 2
    SMALL = 3


def classify_catalog(catalog: list[Barrel]) -> CatalogType:
    '''Classifies the catalog into one of three types: LARGE, MEDIUM, SMALL'''
    best_value = get_best_value(BARREL_TYPES[0], catalog)

    if best_value.ml_per_barrel == 10000:
        return CatalogType.LARGE
    elif best_value.ml_per_barrel == 2500:
        return CatalogType.MEDIUM
    elif best_value.ml_per_barrel == 500:
        return CatalogType.SMALL
    else: 
        logger.error("Unknown Catalog Type", extra={"catalog": catalog})

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

def get_best_value(barrel_type: list[int], catalog: list[Barrel]) -> Barrel:
    '''Returns the best value barrel of the given type, given a catalog of barrels.'''
    return max(filter(type_must_be(barrel_type),catalog), key=ml_to_gold_ratio, default=None)

def determine_barrel_we_have_least_of(barrel_stock: BarrelDelta, catalog: list[Barrel]) -> list[int]:
    '''Catalog must not be empty'''
    
    least_barrel_type = None
    for barrel_type in BARREL_TYPES:
        if len(list(filter(type_must_be(barrel_type), catalog))) == 0:
            continue # Skip if we can't buy any of this type
        if least_barrel_type is None:
            least_barrel_type = barrel_type
        elif barrel_stock.to_array()[barrel_type.index(1)] < barrel_stock.to_array()[least_barrel_type.index(1)]:
            least_barrel_type = barrel_type
    
    return least_barrel_type


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

def get_total_shop_equity(barrel_stock: BarrelDelta, potion_stock: list[PotionEntry], gold: int):
    # Assume we bought small barrels
    # And we sell for exactly list potion price

    gold_per_barrel_ml = 100/500
    blue_gold_per_barrel_ml = 120/500

    equity = gold
    
    equity += barrel_stock.red_ml * gold_per_barrel_ml
    equity += barrel_stock.green_ml * gold_per_barrel_ml
    equity += barrel_stock.blue_ml* blue_gold_per_barrel_ml

    for potion in potion_stock:
        sell_price = potion.quantity * potion.price
        equity += sell_price
    
    return equity

def filter_barrels_within_gold(barrels: list[Barrel], gold: int) -> list[Barrel]:
    return list(filter(lambda a: a.price <= gold, barrels))

@dataclass
class TimelineEvent:
    '''Includes the start/end of a timeline event, and the day of the week it occurs on.
    INCLUSIVE, the "END" date is the last day which event will occur'''
    day_of_week: int
    tick: int

    def currently_before_ticks(self, current_dow: int, current_ticks: int, before_tick_range: int) -> bool:
        '''Returns true if the event is within the given number of ticks.'''
        # Must take into account the start of the event, the wrap around of day
        # of the week and that there's 12 ticks in a day
        '''Sat(6) is within 12 ticks of Sun()
        '''

        event_week_tick = self.day_of_week * 12 + self.tick

        current_week_tick = current_dow * 12 + current_ticks

        # Check for next weeks' event, since we've already passed it
        if event_week_tick < current_week_tick:
            event_week_tick += 7 * 12

        return (event_week_tick - current_week_tick) <= before_tick_range

def get_budget_ratio(day_of_week: int, tick: int, catalog: list[Barrel]) -> float:
    '''Returns the budget ratio for the given day of the week and tick.
    Day of week, Mon=0, Sun=6. Tick = (Hour in PST - 1) / 2'''

    large_barrels_start = TimelineEvent(6, 8)
    medium_start = TimelineEvent(5, 8)

    classification = classify_catalog(catalog)

    # ALWAYS buy all LARGE barrels
    if classification == CatalogType.LARGE:
        return 1.0
    
    # If we're before the large barrel event, only use 20% of our gold on any tick
    if large_barrels_start.currently_before_ticks(day_of_week, tick, 12):
        return 0.2
    
    # Always buy Medium (Only triggers after large barrels)
    if classification == CatalogType.MEDIUM:
        return 1.0

    # If we're before the medium barrel event, only use 50% of our gold on any tick
    if medium_start.currently_before_ticks(day_of_week, tick, 12):
        return 0.5
    
    # Otherwise just use 100% of our gold
    return 1.0


def barrel_planner(day_of_week: int, tick: int, gold: int, barrel_stock: BarrelStock, catalog: list[Barrel], potion_stock: list[PotionEntry]) -> list[Barrel]:
    '''Logic for buying barrels, given a budget, current barrel stock, and a catalog of barrels to buy from.
    
    Goals: Most spread of barrels possible to capture the most customers.'''
    catalog = copy.deepcopy(catalog)
    barrel_stock: BarrelDelta = barrel_stock.to_delta()
    budget = int(gold * get_budget_ratio(day_of_week, tick, catalog))

    target_ml = 30000

    barrels_to_buy = []

    shop_equity = get_total_shop_equity(barrel_stock, potion_stock, gold)

    # Remove all barrels that aren't the best value for color
    # Prevents us from buying MINI barrels
    # We use shop equity so we can always afford a barrel
    for barrel_type in BARREL_TYPES:
        best_value_barrel = get_best_value(barrel_type, filter_barrels_within_gold(catalog, shop_equity))
        
        for barrel in filter(type_must_be(barrel_type),catalog[:]):
            if barrel != best_value_barrel:
                catalog.remove(barrel)

    while True:
        # If we buy/skip every barrel, break
        if len(catalog) == 0:
            break

        # If we can't afford cheapest barrel, break
        if min(catalog, key=price).price > budget:
            break

        # If we have enough of every barrel, break
        if min(barrel_stock.to_array()) >= target_ml:
            break

        # Determine barrel type that we have the least of
        least_barrel_type = determine_barrel_we_have_least_of(barrel_stock, catalog)

        # Remove from catalog if we are at capacity for this type
        if barrel_stock.to_array()[least_barrel_type.index(1)] >= target_ml:
            # If we have enough of this type, skip it
            for barrel in filter(type_must_be(barrel_type),catalog[:]):
                    catalog.remove(barrel)
            continue

        # Find best value barrel for potion type
        best_value_barrel = get_best_value(least_barrel_type, catalog)

        # See if we can afford it
        if best_value_barrel.price > budget:
            # Since we can't afford one of these, we can't afford any of them
            catalog.remove(best_value_barrel)
            continue
            
        # Yay we can afford it, so let's buy one
        buy_one_barrel(best_value_barrel, barrels_to_buy, catalog)
        barrel_stock.add_stock(best_value_barrel.potion_type, best_value_barrel.ml_per_barrel, 1)
        budget -= best_value_barrel.price

    return list(barrels_to_buy)