import logging
import logging.handlers

from config.settings import settings


def configure_logging() -> None:
    log_dir = settings.LOG_DIR
    file_logging_available = True
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        file_logging_available = False

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if file_logging_available and not _has_named_handler(root_logger, "cv_assistant_file"):
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.name = "cv_assistant_file"
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            file_logging_available = False

    if not _has_named_handler(root_logger, "cv_assistant_console"):
        console_handler = logging.StreamHandler()
        console_handler.name = "cv_assistant_console"
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    for noisy_logger in ("httpx", "asyncio", "chromadb", "sentence_transformers"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    if file_logging_available:
        root_logger.info("Logging configured")
    else:
        root_logger.warning("File logging is unavailable; using console logging only")


def _has_named_handler(logger: logging.Logger, name: str) -> bool:
    return any(getattr(handler, "name", None) == name for handler in logger.handlers)
