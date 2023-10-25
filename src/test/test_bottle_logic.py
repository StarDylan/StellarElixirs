import src.logic.bottle_logic as bl
from src.models import BarrelStock, PotionEntry, PotionType
from typing import Callable


def type(potion: PotionEntry) -> PotionType:
    return potion.potion_type
def num(potion: PotionEntry) -> int:
    return potion.quantity
def filter_type(color: PotionEntry) -> Callable[[PotionEntry], bool]:
    def type_filterer(potion: PotionEntry) -> bool:
        return potion.potion_type == color.potion_type
    return type_filterer

RED = PotionEntry(PotionType(100,0,0,0), 0, "RED", 45, 80)
GREEN = PotionEntry(PotionType(0,100,0,0), 0, "GREEN", 45, 60)
BLUE = PotionEntry(PotionType(0,0,100,0), 0, "BLUE", 50, 10)
DARK = PotionEntry(PotionType(0,0,0,100), 0, "DARK", 75, 20)
PURPLE = PotionEntry(PotionType(50,0,50,0), 0, "PURPLE", 45, 30)
YELLOW = PotionEntry(PotionType(50,50,0,0), 0, "YELLOW", 45, 40)
CYAN = PotionEntry(PotionType(0,50,50,0), 0, "CYAN", 50, 60)

def test_bottle_one_red():
    barrel_stock = BarrelStock(100,0,0,0)
    potential_potions_and_stock = [RED, GREEN, BLUE, DARK, PURPLE, YELLOW, CYAN]

    plan = bl.bottle_planner(barrel_stock, potential_potions_and_stock)
    assert RED.potion_type in map(type, plan)

def test_only_bottle_until_300():
    barrel_stock = BarrelStock(30 * 100,0,0,0)

    potential_potions_and_stock = [
        RED.with_quantity(0).with_desired_qty(100), 
        GREEN.with_quantity(100).with_desired_qty(100), 
        BLUE.with_quantity(100).with_desired_qty(100), 
        DARK.with_quantity(80).with_desired_qty(100),
    ]

    plan = bl.bottle_planner(barrel_stock, potential_potions_and_stock)
    
    assert sum(map(num, plan)) <= 20

def test_equal_bottling():
    barrel_stock = BarrelStock(3*100,0, 9*100, 0)

    potential_potions_and_stock = [
        RED.with_quantity(6).with_desired_qty(50), 
        PURPLE.with_quantity(0).with_desired_qty(50), 
        BLUE.with_quantity(0).with_desired_qty(50)
    ]

    plan = bl.bottle_planner(barrel_stock, potential_potions_and_stock)
    
    assert sum(map(num, filter(filter_type(RED), plan))) == 0
    assert sum(map(num, filter(filter_type(PURPLE), plan))) == 6
    assert sum(map(num, filter(filter_type(BLUE), plan))) == 6

def test_not_bottling_if_no_stock():
    barrel_stock = BarrelStock(0,0,0,0)

    potential_potions_and_stock = [
        RED.with_quantity(6).with_desired_qty(50), 
        PURPLE.with_quantity(0).with_desired_qty(50), 
        BLUE.with_quantity(0).with_desired_qty(50)
    ]

    plan = bl.bottle_planner(barrel_stock, potential_potions_and_stock)
    
    assert len(plan) == 0

def test_dont_go_over_desired_qty():
    barrel_stock = BarrelStock(1000,0,0,0)

    potential_potions_and_stock = [
        RED.with_quantity(55).with_desired_qty(50), 
        PURPLE.with_quantity(0).with_desired_qty(50), 
        BLUE.with_quantity(0).with_desired_qty(50)
    ]

    plan = bl.bottle_planner(barrel_stock, potential_potions_and_stock)
    
    assert len(plan) == 0