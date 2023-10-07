import os
import logging
from fastapi import FastAPI
import graypy
import json
from asgi_correlation_id import CorrelationIdFilter, CorrelationIdMiddleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class StellarElixirId(logging.Filter):
    def __init__(self):
        is_prod = os.environ.get("IS_PROD")
        if is_prod:
            self.is_prod = "True"
        else:
            self.is_prod = "False"
    def filter(self, record):
        record.app = "Stellar Elixirs"
        record.prod = self.is_prod
        return True


class LogFailureMiddleware:
    async def __call__(self, request: Request, call_next):
        logger = logging.getLogger("middleware")

        response = None

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error("Request Failed", exc_info=e)
            return Response("Internal server error", status_code=500)

        
        return response

async def log_request_info(request: Request):
        
        logger = logging.getLogger("router")
        request_body = await request.body()

        header_dict = {}
        for item in request.headers.items():
            header_dict[item[0]] = item[1]

        query_dict = {}
        for item in request.query_params.items():
            query_dict[item[0]] = item[1]

        logger.info(
            f"{request.method} request to {request.url.path}",
            extra={"headers": json.dumps(header_dict), 
                   "body": request_body,
                   "path": request.url.path,
                   "path_params": json.dumps(request.path_params), 
                   "query_params": json.dumps(query_dict)}
        )


def init_logger(app: FastAPI):
    graylog_url = os.environ.get("GRAYLOG_URL")
    graylog_port = os.environ.get("GRAYLOG_PORT")
    
    root_logger = logging.getLogger()

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(BaseHTTPMiddleware, dispatch=LogFailureMiddleware())
        
   

    if graylog_url and graylog_port:
        if graylog_port.isdigit():
            graylog_port = int(graylog_port)
        else:
            logging.warning("Graylog port is not a number")
            exit(1)

        logging.info("Enabling Graylog!")


        gelf_handler = graypy.GELFTCPHandler(graylog_url, int(graylog_port), 
            level_names=True)
        gelf_handler.addFilter(StellarElixirId())
        gelf_handler.addFilter(CorrelationIdFilter())

        root_logger.addHandler(gelf_handler)

        
    else:
        logging.warning("Graylog not enabled")
    

    logging.debug('Finished Log Initialization')