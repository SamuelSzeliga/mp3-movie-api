import logging

logger = logging.getLogger(__name__)

def setup_logging(verbose=False):
    """Configure logging for the pipeline."""
    if verbose == False:
        lvl=logging.INFO
    else:
        lvl=logging.DEBUG
    logging.basicConfig(
    level=lvl,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    )