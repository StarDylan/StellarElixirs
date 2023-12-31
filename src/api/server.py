from fastapi import FastAPI, exceptions, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.api import audit, carts, catalog, bottler, barrels, admin
from src.logger_init import init_logger, log_request_info
import json
import logging
import dotenv
import os
from starlette.middleware.cors import CORSMiddleware

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
    dependencies=[Depends(log_request_info)],
    root_path=os.environ.get('ROOT_PATH')
)

logging.getLogger().setLevel(logging.INFO)

(log_request_info) = init_logger(app)

origins = ["https://potion-exchange.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(audit.router)
app.include_router(carts.router)
app.include_router(catalog.router)
app.include_router(bottler.router)
app.include_router(barrels.router)
app.include_router(admin.router)

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