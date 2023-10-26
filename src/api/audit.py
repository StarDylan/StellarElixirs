from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
import logging

logger = logging.getLogger("audit")

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """

    with db.engine.begin() as conn:
        
        total_potions = 0
        for potion in db.get_potions(conn):
            total_potions += potion.quantity

        ml_in_barrels = db.get_barrel_stock(conn).all_ml()
        gold = db.get_gold(conn)

    logger.info("Being Audited", extra={
        "number_of_potions": total_potions, 
        "ml_in_barrels": ml_in_barrels,
        "gold": gold})

    return {"number_of_potions": total_potions, 
            "ml_in_barrels": ml_in_barrels, 
            "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """

    print(audit_explanation)

    audit_adapter = logging.LoggerAdapter(logger, {
            "match_gold": str(audit_explanation.gold_match),
            "match_barrels": str(audit_explanation.barrels_match),
            "match_potions": str(audit_explanation.potions_match)})

    if audit_explanation.barrels_match \
        and audit_explanation.gold_match \
        and audit_explanation.potions_match:

        audit_adapter.info("Audit returned OK")
    else:
        audit_adapter.error("Audit returned failure")
        

    return "OK"
