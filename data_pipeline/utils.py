import logging
from pathlib import Path
import sys


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


def validate_input(filepath):
    """Check whether the input path exists and is a file."""
    if Path(filepath).is_file():
        logger.info(f"Input file validated: {filepath}")
    else:
        logger.error(f"Input file not found: {filepath}")
        sys.exit(1)