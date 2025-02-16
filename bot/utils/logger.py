import logging


def configure_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the entire application.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
