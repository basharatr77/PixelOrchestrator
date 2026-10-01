from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "app" / "config.json"

REQUIRED_KEYS = ("host", "port", "database")


def load_config():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError("Configuration file not found") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid configuration JSON") from exc

    if not isinstance(config, dict):
        raise ValueError("Invalid configuration object")

    unknown = [key for key in config if key not in REQUIRED_KEYS]
    if unknown:
        raise ValueError("Unknown configuration key(s): " + ", ".join(unknown))

    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ValueError(
            "Missing required configuration key(s): " + ", ".join(missing)
        )

    if not isinstance(config["host"], str) or not config["host"].strip():
        raise ValueError("Invalid host configuration")

    config["host"] = config["host"].strip()

    if not isinstance(config["port"], int) or isinstance(config["port"], bool):
        raise ValueError("Invalid port configuration")

    if not 1 <= config["port"] <= 65535:
        raise ValueError("Invalid port configuration: port must be 1-65535")

    if not isinstance(config["database"], str) or not config["database"].strip():
        raise ValueError("Invalid database configuration")

    database = Path(config["database"].strip())
    if not database.is_absolute():
        database = PROJECT_ROOT / database

    config["database"] = str(database)
    return config
