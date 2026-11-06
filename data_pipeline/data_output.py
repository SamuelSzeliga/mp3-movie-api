import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def save_data(df, filepath):
    """
    Save a DataFrame as a CSV file.
    """
    output_directory = Path(filepath)
    output_directory.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_directory, index=False)
    
    logger.debug(f"Data Output: {len(df)} rows saved, output path: {output_directory}")
    return output_directory