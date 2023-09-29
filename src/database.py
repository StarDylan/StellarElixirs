import os
import dotenv
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)


def get_gold():
    """ """
    with engine.begin() as connection:
        result = connection.execute(
            "SELECT gold FROM global_inventory"
        ).one()
        return result[0]
    
def add_gold(gold_to_add: int):
    """ """
    with engine.begin() as connection:
        connection.execute(
            f"UPDATE global_inventory SET gold=gold + {gold_to_add}"
        )

def get_red_ml():
    """ """
    with engine.begin() as connection:
        result = connection.execute(
            "SELECT num_red_ml FROM global_inventory"
        ).one()
        return result[0]

def add_red_ml(red_ml_to_add: int):
    """ """
    with engine.begin() as connection:
        connection.execute(
            f"UPDATE global_inventory SET num_red_ml=num_red_ml + {red_ml_to_add}"
        )

def get_red_potions():
    """ """
    with engine.begin() as connection:
        result = connection.execute(
            "SELECT num_red_potions FROM global_inventory"
        ).one()
        return result[0]
    
def add_red_potions(red_potions_to_add: int):
    """ """
    with engine.begin() as connection:
        connection.execute(
            f"UPDATE global_inventory SET num_red_potions=num_red_potions + {red_potions_to_add}"
        )