import logging
import sys

def setup_logging(debug: bool = False):
    """Sets up the logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Simple format that works well in a CLI
    # If debug is on, include the logger name and line number
    if debug:
        fmt = "%(levelname)s: [%(name)s:%(lineno)d] %(message)s"
    else:
        fmt = "%(message)s"
        
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Silence third-party loggers if needed
    if not debug:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str):
    """Gets a logger for a specific module."""
    return logging.getLogger(f"anvil.{name}")
