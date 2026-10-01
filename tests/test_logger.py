from pathlib import Path

import app.logger as logger_module


def test_logger_uses_project_log_directory():
    project_root = Path(logger_module.__file__).resolve().parents[1]
    expected_log = project_root / "logs" / "pixel.log"

    assert logger_module.LOG_FILE == expected_log


def test_logger_has_file_handler_for_project_log():
    project_root = Path(logger_module.__file__).resolve().parents[1]
    expected_log = project_root / "logs" / "pixel.log"

    matching_handlers = [
        handler
        for handler in logger_module.logger.handlers
        if getattr(handler, "baseFilename", None)
        and Path(handler.baseFilename).resolve() == expected_log
    ]

    assert matching_handlers


def test_logger_keeps_structured_basic_record_format():
    assert logger_module.LOG_FORMAT
    assert "%(asctime)s" in logger_module.LOG_FORMAT
    assert "%(levelname)s" in logger_module.LOG_FORMAT
    assert "%(message)s" in logger_module.LOG_FORMAT
