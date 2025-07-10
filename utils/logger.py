import logging
import sys

# ANSI escape codes for colors
LOG_COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[41m",  # Red background
}
RESET_COLOR = "\033[0m"


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = LOG_COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{RESET_COLOR}"


def setup_logging(debug: bool = False):
    """Set up logging with file and function name in the format, with colored output."""
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []  # Remove any existing handlers
    root_logger.addHandler(handler)
    # Suppress noisy library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)


def get_logger(name=None):
    return logging.getLogger(name)
