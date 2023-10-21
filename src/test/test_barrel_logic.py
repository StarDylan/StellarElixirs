import src.logic.barrel_logic as bl
from src.models import Barrel, BarrelStock
import json
from typing import Iterable

LARGE_DARK_BARREL = Barrel(**{"sku": "LARGE_DARK_BARREL", "price": 750, "quantity": 10, "potion_type": [0, 0, 0, 1], "ml_per_barrel": 10000})
LARGE_RED_BARREL = Barrel(**{"sku": "LARGE_RED_BARREL", "price": 500, "quantity": 30, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 10000})
LARGE_GREEN_BARREL = Barrel(**{"sku": "LARGE_GREEN_BARREL", "price": 400, "quantity": 30, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 10000})
LARGE_BLUE_BARREL = Barrel(**{"sku": "LARGE_BLUE_BARREL", "price": 600, "quantity": 30, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 10000})
MEDIUM_RED_BARREL = Barrel(**{"sku": "MEDIUM_RED_BARREL", "price": 250, "quantity": 10, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 2500})
MEDIUM_GREEN_BARREL = Barrel(**{"sku": "MEDIUM_GREEN_BARREL", "price": 250, "quantity": 10, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 2500})
MEDIUM_BLUE_BARREL = Barrel(**{"sku": "MEDIUM_BLUE_BARREL", "price": 300, "quantity": 10, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 2500})
SMALL_RED_BARREL = Barrel(**{"sku": "SMALL_RED_BARREL", "price": 100, "quantity": 10, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 500})
SMALL_GREEN_BARREL = Barrel(**{"sku": "SMALL_GREEN_BARREL", "price": 100, "quantity": 10, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 500})
SMALL_BLUE_BARREL = Barrel(**{"sku": "SMALL_BLUE_BARREL", "price": 120, "quantity": 10, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 500})
MINI_RED_BARREL =  Barrel(**{"sku": "MINI_RED_BARREL", "price": 60, "quantity": 1, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 200})
MINI_GREEN_BARREL = Barrel(** {"sku": "MINI_GREEN_BARREL", "price": 60, "quantity": 1, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 200})
MINI_BLUE_BARREL = Barrel(**{"sku": "MINI_BLUE_BARREL", "price": 60, "quantity": 1, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 200})

"""[{"sku": "MEDIUM_RED_BARREL", "price": 250, "quantity": 10, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 2500}
{"sku": "SMALL_RED_BARREL", "price": 100, "quantity": 10, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 500}
{"sku": "MEDIUM_GREEN_BARREL", "price": 250, "quantity": 10, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 2500}
{"sku": "SMALL_GREEN_BARREL", "price": 100, "quantity": 10, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 500}
{"sku": "MEDIUM_BLUE_BARREL", "price": 300, "quantity": 10, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 2500}
{"sku": "SMALL_BLUE_BARREL", "price": 120, "quantity": 10, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 500}
{"sku": "MINI_RED_BARREL", "price": 60, "quantity": 1, "potion_type": [1, 0, 0, 0], "ml_per_barrel": 200}
{"sku": "MINI_GREEN_BARREL", "price": 60, "quantity": 1, "potion_type": [0, 1, 0, 0], "ml_per_barrel": 200}
{"sku": "MINI_BLUE_BARREL", "price": 60, "quantity": 1, "potion_type": [0, 0, 1, 0], "ml_per_barrel": 200}]
"""

small_catalog = [SMALL_RED_BARREL, SMALL_GREEN_BARREL, SMALL_BLUE_BARREL, 
                          MINI_RED_BARREL, MINI_GREEN_BARREL, MINI_BLUE_BARREL]

medium_catalog = [MEDIUM_RED_BARREL, MEDIUM_GREEN_BARREL, MEDIUM_BLUE_BARREL,
                            SMALL_RED_BARREL, SMALL_GREEN_BARREL, SMALL_BLUE_BARREL,
                            MINI_RED_BARREL, MINI_GREEN_BARREL, MINI_BLUE_BARREL]

large_catalog = [LARGE_RED_BARREL, LARGE_GREEN_BARREL, LARGE_BLUE_BARREL,
                            MEDIUM_RED_BARREL, MEDIUM_GREEN_BARREL, MEDIUM_BLUE_BARREL,
                            SMALL_RED_BARREL, SMALL_GREEN_BARREL, SMALL_BLUE_BARREL,
                            MINI_RED_BARREL, MINI_GREEN_BARREL, MINI_BLUE_BARREL]


def skus(plan: list[Barrel]) -> Iterable[str]:
    return map(lambda a: a.sku, plan)

def check_for_valid_plan(plan: list[Barrel], catalog: list[Barrel],):
    total_qty_bought = {}
    for barrel in plan:
        if barrel.sku in total_qty_bought:
            assert False, "Same sku was listed multiple times"
        if barrel.sku not in map(lambda a: a.sku, catalog):
            assert False, "Sku was not in catalog"

        total_qty_bought[barrel.sku] = barrel.quantity
    
    # Check to make sure we don't buy more than available
    for catalog_barrel in catalog:
        assert total_qty_bought.get(catalog_barrel.sku, 0) <= catalog_barrel.quantity

def calculate_gold_spent(plan: list[Barrel]) -> int:
    return sum(map(lambda a: a.price * a.quantity, plan))

def test_barrel_logic_buys_a_barrel_when_starting_out():
    plan = bl.barrel_planner(100, 
                      BarrelStock(0,0,0,0), 
                      small_catalog)
    
    check_for_valid_plan(plan, small_catalog)

    assert len(plan) > 0
    

def test_barrel_logic_buys_a_mix_when_available():
    plan = bl.barrel_planner(320, 
                      BarrelStock(0,0,0,0), 
                      small_catalog)
    
    check_for_valid_plan(plan, small_catalog)

    assert SMALL_RED_BARREL.sku in skus(plan)
    assert SMALL_GREEN_BARREL.sku in skus(plan)
    assert SMALL_BLUE_BARREL.sku in skus(plan)

def test_barrel_logic_doesnt_buy_if_not_enough_gold():
    plan = bl.barrel_planner(50, 
                      BarrelStock(0,0,0,0), 
                      small_catalog)
    
    check_for_valid_plan(plan, small_catalog)

    assert len(plan) == 0, "Shouldn't buy anything if not enough gold"