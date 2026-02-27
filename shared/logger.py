import logging
import sys,os
from pythonjsonlogger import jsonlogger

def setup_logging(service_name: str) -> logging.Logger:

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    

    # to prevent duplicate handlers
    if logger.handlers:
        return logger
    
    log_format = (
        "%(asctime)s %(levelname)s %(name)s "
        "service=%(service)s %(message)s"
        )
    
#    formatter = logging.Formatter(log_format)   this is for normal formatter 
    formatter = jsonlogger.JsonFormatter(log_format)  # this is for that json format

    # stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


    # file handler
    if os.getenv("LOG_ENV" , "local") == "local":
        file_handler = logging.FileHandler(f"{service_name}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # to inject service name into log records
    return logging.LoggerAdapter(logger, {"service": service_name})