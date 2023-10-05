import os
import logging
import graypy
import time
import random
from asgi_correlation_id import CorrelationIdFilter
from fastapi import Request, Response

class StellarElixirId(logging.Filter):
    def __init__(self):
        is_prod = os.environ.get("IS_PROD")
        if is_prod:
            self.is_prod = True
        else:
            self.is_prod = False
    def filter(self, record):
        record.app = "Stellar Elixirs"
        record.prod = self.is_prod
        return True


def init_logger(app):
    graylog_url = os.environ.get("GRAYLOG_URL")
    graylog_port = os.environ.get("GRAYLOG_PORT")
    
    root_logger = logging.getLogger()

    async def log_request_info(request: Request):
        
        logger = logging.LoggerAdapter(logging.getLogger("router"))
        request_body = await request.body()

        logger.info(
            f"{request.method} request to {request.url.path}",
            extra={"Headers": request.headers, 
                   "Body": request_body,
                   "Path Params": request.path_params, 
                   "Query Params": request.query_params,
                   "Cookies": request.cookies}
        )


        
    @app.middleware("http")
    async def log_failures(request: Request, call_next):
        logger = logging.LoggerAdapter(logging.getLogger("middleware"))

        response = None

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error("Request Failed", exc_info=e)
            return Response("Internal server error", status_code=500)

        
        return response

    if graylog_url and graylog_port:
        if graylog_port.isdigit():
            graylog_port = int(graylog_port)
        else:
            logging.warning("Graylog port is not a number")
            exit(1)

        logging.info("Enabling Graylog!")


        gelf_handler = graypy.GELFTCPHandler(graylog_url, int(graylog_port))
        root_logger.addHandler(gelf_handler)

        
        root_logger.addFilter(StellarElixirId())
    else:
        logging.warning("Graylog not enabled")
    
    
    root_logger.addFilter(CorrelationIdFilter())


    logging.info('Finished Log Initialization')

    return (log_request_info)
