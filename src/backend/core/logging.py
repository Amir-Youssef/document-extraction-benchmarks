import logging
import sys

from backend.core.config import Settings


def setup_logging(settings: Settings) -> None:
    log_level = settings.log_level.upper()

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(settings.app_name)
    logger.info(
        "Logging configured — level=%s, environment=%s",
        log_level,
        settings.environment,
    )
