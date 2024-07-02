import logging

def setup_logging(verbose):
    logging.basicConfig(level=logging.WARN,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.WARN)
    return logging.getLogger(__name__)