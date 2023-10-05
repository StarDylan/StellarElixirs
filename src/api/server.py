from fastapi import FastAPI, exceptions, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from asgi_correlation_id import CorrelationIdMiddleware
from src.api import audit, carts, catalog, bottler, barrels, admin
from src.logger_init import init_logger
import json
import logging
import dotenv

description = """
Shine Bright with Stellar Elixirs: Your Celestial Source for Magical Potions
"""

dotenv.load_dotenv()


app = FastAPI(
    title="Stellar Elixirs",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Dylan Starink",
        "email": "dstarink@calpoly.edu",
    },
)

(log_request_info) = init_logger(app)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(audit.router, dependencies=[Depends(log_request_info)])
app.include_router(carts.router, dependencies=[Depends(log_request_info)])
app.include_router(catalog.router, dependencies=[Depends(log_request_info)])
app.include_router(bottler.router, dependencies=[Depends(log_request_info)])
app.include_router(barrels.router, dependencies=[Depends(log_request_info)])
app.include_router(admin.router, dependencies=[Depends(log_request_info)])

@app.exception_handler(exceptions.RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    logging.error(f"The client sent invalid data!: {exc}")
    exc_json = json.loads(exc.json())
    response = {"message": [], "data": None}
    for error in exc_json:
        response['message'].append(f"{error['loc']}: {error['msg']}")

    return JSONResponse(response, status_code=422)

@app.get("/")
async def root():
    return {"message": "Welcome to Stellar Elixirs!"}