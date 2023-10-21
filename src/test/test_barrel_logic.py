import src.logic.barrel_logic as bl
from models import BarrelStock
from src.api.barrels import Barrel

def test_barrel_logic_buys_a_barrel_when_starting_out():
    plan = bl.barrel_planner(100, 
                      BarrelStock.init_zero(), 
                      [Barrel(sku="test", ml_per_barrel=100, potion_type=[1,0,0,0], price=100, quantity=1)])

    assert len(plan) == 0
    
    assert plan[0].sku == "test"
    assert plan[0].ml_per_barrel == 100
    assert plan[0].potion_type == [1,0,0,0]
    assert plan[0].price == 100
    assert plan[0].quantity == 1