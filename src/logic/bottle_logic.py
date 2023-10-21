from src.models import BarrelDelta, BarrelStock, PotionEntry

def currrent_to_wanted_qty_ratio(entry: PotionEntry) -> float:
    '''Returns the ratio of the current quantity to the wanted quantity.
    Where 1.0 means we have the desired quantity, and 0.0 means we have none.'''
    if entry.desired_qty == 0:
        return float("inf")
    
    return entry.quantity / entry.desired_qty

def barrel_needed(potion: PotionEntry) -> BarrelDelta:
    '''Returns the amount of each color needed to make the given potion.'''
    return BarrelDelta.from_array(potion.potion_type.to_array())

def make_one_potion(potion: PotionEntry, potions_to_bottle: list[PotionEntry]):
    '''Modifies the barrel stock to reflect the bottling of the given potion.
    Also will add it to the specified list of potions to bottle.'''
    # Check if potion already in potions_to_bottle list
    existing_potion = next(filter(lambda a: a.potion_type == potion.potion_type, potions_to_bottle), None)
    
    number_of_bottles = 1

    if existing_potion is not None:
        number_of_bottles += existing_potion.quantity
        potions_to_bottle.remove(existing_potion)

    potions_to_bottle.append(PotionEntry(potion.potion_type, number_of_bottles, 
                                         potion.sku, potion.price, potion.desired_qty))

def num_potions(potion: PotionEntry) -> int:
    '''Returns the number of potions in an entry'''
    return potion.quantity


def bottle_planner(barrel_stock: BarrelStock, potential_and_current_potions: list[PotionEntry]) -> list[PotionEntry]:
    
    barrel_stock: BarrelDelta = barrel_stock.to_delta()

    current_num_potions = sum(map(num_potions, potential_and_current_potions)) 

    potions_to_bottle = []

    while True:   
        num_potions_in_plan = sum(map(num_potions, potions_to_bottle)) 

        # We can only have 300 potions total
        if (current_num_potions + num_potions_in_plan) == 300:
            break

        potions_we_can_make = list(filter(lambda a: barrel_stock.has_at_least(barrel_needed(a)), potential_and_current_potions))

        # Can we make any of our potions?
        if len(potions_we_can_make) == 0:
            break
            
        # Lets find the potion that we are the furthest from our
        # desired qty
        potion_we_have_least_of = min(potions_we_can_make, key=currrent_to_wanted_qty_ratio)

        make_one_potion(potion_we_have_least_of, potions_to_bottle)
        barrel_stock.remove_stock(potion_we_have_least_of.potion_type, 1)

    return potions_to_bottle