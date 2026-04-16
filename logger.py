import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / "Library" / "Logs" / "epubtoaudio"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "epubtoaudio.log"


def setup_logging():
    logger = logging.getLogger("epubtoaudio")
    logger.setLevel(logging.INFO)
    
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    handler.suffix = "%Y-%m-%d"
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.addHandler(console_handler)
    
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()
