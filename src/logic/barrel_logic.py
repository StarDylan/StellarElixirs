from src.api.barrels import Barrel
from src.models import BarrelStock
import copy



def barrel_planner(gold: int, barrel_stock: BarrelStock, catalog: list[Barrel]) -> list[Barrel]:
    
    catalog = copy.deepcopy(catalog)
    barrel_stock = copy.copy(barrel_stock)

    barrels_to_buy = []

    # Buy first catalog item
    barrels_to_buy.append(catalog.pop(0))


    return barrels_to_buy