import src.logic.barrel_logic as bl
from src.models import Barrel, BarrelDelta, BarrelStock, PotionEntry, PotionType
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

        if barrel.quantity <= 0:
            assert False, "Barrel Qty was less than 0"
    
    # Check to make sure we don't buy more than available
    for catalog_barrel in catalog:
        assert total_qty_bought.get(catalog_barrel.sku, 0) <= catalog_barrel.quantity

def calculate_gold_spent(plan: list[Barrel]) -> int:
    return sum(map(lambda a: a.price * a.quantity, plan))

def test_barrel_logic_buys_a_barrel_when_starting_out():
    plan = bl.barrel_planner(3, 0, 100, 
                      BarrelStock(0,0,0,0), 
                      small_catalog, [])
    
    check_for_valid_plan(plan, small_catalog)

    assert len(plan) > 0
    
def test_barrel_logic_buys_a_barrel_when_starting_out_with_medium_catalog():
    plan = bl.barrel_planner(3, 0, 100, 
                      BarrelStock(0,0,0,0), 
                      medium_catalog, [])
    
    check_for_valid_plan(plan, medium_catalog)

    assert len(plan) > 0


def test_barrel_logic_buys_a_mix_when_available():
    plan = bl.barrel_planner(3, 0, 320, 
                      BarrelStock(0,0,0,0), 
                      small_catalog, [])
    
    check_for_valid_plan(plan, small_catalog)

    assert SMALL_RED_BARREL.sku in skus(plan)
    assert SMALL_GREEN_BARREL.sku in skus(plan)
    assert SMALL_BLUE_BARREL.sku in skus(plan)

def test_barrel_logic_doesnt_buy_if_not_enough_gold():
    plan = bl.barrel_planner(5, 0, 50, 
                      BarrelStock(0,0,0,0), 
                      small_catalog, [])
    
    check_for_valid_plan(plan, small_catalog)

    assert len(plan) == 0, "Shouldn't buy anything if not enough gold"

def test_buy_mini_barrel_if_broke():
    plan = bl.barrel_planner(3, 0, 70, 
                            BarrelStock(0,0,0,0), 
                            small_catalog, [])

    check_for_valid_plan(plan, small_catalog)

    assert len(plan) == 1

def test_dont_buy_mini_barrel_if_rich():
    plan = bl.barrel_planner(3, 0, 70, 
                            BarrelStock(1000,0,0,0), 
                            small_catalog, [])

    check_for_valid_plan(plan, small_catalog)

    assert len(plan) == 0, "Shouldn't buy mini barrel when rich, but no gold"

def test_dont_buy_mini_barrel_if_rich_in_potions():
    plan = bl.barrel_planner(3, 0, 70, 
                            BarrelStock(0,0,0,0), 
                            small_catalog, 
                            [PotionEntry(PotionType(100,0,0,0), 50, "RED", 50, 60)])

    check_for_valid_plan(plan, small_catalog)

    assert len(plan) == 0, "Shouldn't buy mini barrel when rich, but no gold"

def test_special_20_percent_budget():
    plan = bl.barrel_planner(5, 9, 1250, 
                             BarrelStock(0,1000,1000,1000),
                             medium_catalog, [])
    
    check_for_valid_plan(plan, medium_catalog)

    assert plan[0].quantity == 1, "Should buy only 1 barrel"
    assert MEDIUM_RED_BARREL.sku == plan[0].sku, "Should buy red barrel"


def test_special_50_percent_budget():
    plan = bl.barrel_planner(5, 0, 400, 
                             BarrelStock(0,600,600,600),
                             small_catalog, [])
    
    check_for_valid_plan(plan, small_catalog)

    assert plan[0].quantity == 2, "Should buy 2 barrels because 50 percent budget"
    assert SMALL_RED_BARREL.sku == plan[0].sku, "Should buy red barrel"

def test_use_all_gold_when_large_barrels():
    plan = bl.barrel_planner(0, 0, 500, 
                             BarrelStock(0,300,300,300),
                             large_catalog, [])
    
    check_for_valid_plan(plan, large_catalog)

    assert plan[0].quantity == 1
    assert LARGE_RED_BARREL.sku in skus(plan)

def test_use_all_gold_when_medium_barrels_past_large():
    plan = bl.barrel_planner(0, 11, 250, 
                             BarrelStock(0,300,300,300),
                             medium_catalog, [])
    
    check_for_valid_plan(plan, medium_catalog)

    assert plan[0].quantity == 1
    assert MEDIUM_RED_BARREL.sku in skus(plan)


def test_only_buy_up_to_30000_ml():
    plan = bl.barrel_planner(0, 11, 5000, 
                             BarrelStock(29000,40000,40000,40000),
                             medium_catalog, [])
    
    check_for_valid_plan(plan, medium_catalog)

    assert plan[0].quantity == 1
    assert MEDIUM_RED_BARREL.sku in skus(plan)
    assert len(plan) == 1


def test_total_balance():
    plan = bl.barrel_planner(3, 0, 300, 
                             BarrelStock(500,0,0,0),
                             small_catalog, [])
    
    check_for_valid_plan(plan, small_catalog)

    # Should not buy any red, since we have a lot
    assert SMALL_RED_BARREL.sku not in skus(plan)
    assert SMALL_GREEN_BARREL.sku in skus(plan)
    assert SMALL_BLUE_BARREL.sku in skus(plan)



def test_hang():
    plan = bl.barrel_planner(5, 4, 70000, 
        BarrelStock(122756,157206,134538,0),
        small_catalog, 
        [PotionEntry(PotionType(0, 0, 100, 0), 31, "BLUE", 60, 60)])

    assert len(plan) == 0


######################
####### HELPER########
######################

def test_classify_catalog():
    classification = bl.classify_catalog(large_catalog)

    assert classification == bl.CatalogType.LARGE

    classification = bl.classify_catalog(medium_catalog)

    assert classification == bl.CatalogType.MEDIUM

    classification = bl.classify_catalog(small_catalog)

    assert classification == bl.CatalogType.SMALL

def test_timeline_event():
    assert bl.TimelineEvent(0, 5).currently_before_ticks(6, 9, 8)
    assert not bl.TimelineEvent(0, 5).currently_before_ticks(6, 9, 7)

    assert bl.TimelineEvent(5, 3).currently_before_ticks(4, 9, 6)
    assert not bl.TimelineEvent(5, 3).currently_before_ticks(4, 9, 5)

def test_total_shop_equity():
    equity = bl.get_total_shop_equity(BarrelDelta(100, 400, 600, 0), [
        PotionEntry(PotionType(100, 0, 0, 0), 5, "RED", 50, 60),
        PotionEntry(PotionType(0, 0, 100, 0), 8, "BLUE", 65, 60)
    ],
    1000)

    assert equity == 1000 + (100 / (5)) + (400 / 5) + (600 / (500/120)) + (50 * 5) + (8 * 65)
