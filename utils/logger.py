import logging
import os 
from datetime import datetime 


LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "output")
LOG_FILE = os.path.join(LOG_DIR, "logger_run.log")

def get_logger(name: str) -> logging.Logger:
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger 
    
    logger.setLevel(logging.DEBUG)
    
    fmt = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console Handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)
    
    file_h = logging.FileHandler(LOG_FILE, mode = "a", encoding = "utf-8")
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(fmt)
    logger.addHandler(file_h)
    
    return logger
    
    