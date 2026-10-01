from pathlib import Path
import logging


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pixel.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("PixelOrchestrator")
logger.setLevel(logging.INFO)

if not any(
    getattr(handler, "baseFilename", None)
    and Path(handler.baseFilename).resolve() == LOG_FILE
    for handler in logger.handlers
):
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
