import logging
import pandas as pd

logger = logging.getLogger(__name__)

def validate_dataframe(df, required_columns, numeric_columns):
    """
    Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be
    numeric.
    """
    for col in required_columns:
        if not set(required_columns).issubset(df.columns):
            logger.error(f"{required_columns} is missing")
            raise ValueError(f"{required_columns} is missing")

    for col in numeric_columns:
        invalid_rows = []
        for i, value in df[col].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    invalid_rows.append(i)

    logger.warning(f"Removed {len(invalid_rows)} with invalid numeric values in rating")

    df = df.drop(index=invalid_rows)
    logger.debug(f"Validator: {len(df)} rows validated, {len(invalid_rows)} invalid rows")

    #convert to a numeric data type
    df[col] = pd.to_numeric(df[col])
    return df