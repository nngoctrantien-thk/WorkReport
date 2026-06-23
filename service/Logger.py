import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "bot.log",
            encoding="utf8"
        ),
        logging.StreamHandler()
    ]
)

# Tắt log HTTP
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Tắt bớt log của telegram
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True

def get_logger(name):
    return logging.getLogger(name)