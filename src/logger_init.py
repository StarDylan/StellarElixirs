import os
import logging
import graypy
from asgi_correlation_id import CorrelationIdFilter

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


def init_logger():
    graylog_url = os.environ.get("GRAYLOG_URL")
    graylog_port = int(os.environ.get("GRAYLOG_PORT"))

    if graylog_url and graylog_port:
        logging.info("Enabling Graylog!")

        root_logger = logging.getLogger()

        gelf_handler = graypy.GELFUDPHandler(graylog_url, int(graylog_port))
        root_logger.addHandler(gelf_handler)

        
        root_logger.addFilter(StellarElixirId())
    
    
    root_logger.addFilter(CorrelationIdFilter())


    logging.info('Started')
