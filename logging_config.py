import logging
import logging.handlers

from config.settings import settings

FILE_HANDLER_NAME = "cv_assistant_file"
CONSOLE_HANDLER_NAME = "cv_assistant_console"


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

    if file_logging_available and not _has_named_handler(root_logger, FILE_HANDLER_NAME):
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.set_name(FILE_HANDLER_NAME)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            file_logging_available = False

    if not _has_named_handler(root_logger, CONSOLE_HANDLER_NAME):
        console_handler = logging.StreamHandler()
        console_handler.set_name(CONSOLE_HANDLER_NAME)
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
    return any(handler.get_name() == name for handler in logger.handlers)
