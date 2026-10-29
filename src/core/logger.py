import logging

def setup_logger(name="MangaDownloader"):
    """
    Configures and returns a clean logger without saving physical log files.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Console handler only (does not create 'logs' folder or physical files)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(levelname)s]: %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
