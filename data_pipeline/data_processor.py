import logging
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


def remove_duplicates(df):
    """Remove duplicate rows."""

    before = df.copy()

    columns = [col for col in df.columns if col != "id"]
    df = df.drop_duplicates(subset=columns)
    logger.debug(f"Remove duplicates: {len(before)-len(df)} rows removed")
    return df


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    before_df = df.copy()
    if axis == "rows":
        df = df.dropna()
        logger.debug(f"Handle missing: {len(before_df)} -> {len(df)} rows")
    elif axis == "columns":
        df = df.dropna(axis=1)
        logger.debug(f"Handle missing: {len(before_df)} -> {len(df)} columns")
    else:
        logger.error(f"{axis} is unsupported")
        raise ValueError(f"{axis} is unsupported")

    return df


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""

    before = df.copy()
    cleaned_columns = []
    for col in columns:
        if col not in df.columns:
            logger.warning(f"{col} does not exist")
        elif not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"{col} is not numeric")
        else:
            cleaned_columns.append(col)

    if method == "iqr":
        for col in cleaned_columns:
            q1 = df[cleaned_columns].quantile(0.25)
            q3 = df[cleaned_columns].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            df = df[((df[cleaned_columns] >= lower) & (df[cleaned_columns] <= upper)).all(axis=1)]
        logger.debug(f"Method: {method}, Threshold: {threshold}, Number of rows removed: {len(before) - len(df)}")

    elif method == "zscore":
        for col in cleaned_columns:
            mean = df[col].mean()
            std = df[col].std()
            z_scores=(df[col] - mean) / std
            df = df[z_scores.abs() <= threshold]
            logger.debug(f"Method: {method}, Threshold: {threshold}, Number of rows removed: {len(before) - len(df)}")

    else:
        logger.error(f"{method} unsupported method")
        raise ValueError(f"{method} unsupported method")
    
    return df
        

def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""

    processing = config["processing"]
    if processing.get("remove_duplicates", True):
        df = remove_duplicates(df)

    missing = processing.get("missing", {})
    if missing.get("enabled", True):
        axis = missing.get("axis", "rows")
        df = handle_missing(df, axis=axis)

    outliers = processing.get("outliers", {})
    if outliers.get("enabled", False):
        columns = outliers.get("columns", [])
        method = outliers.get("method", "iqr")
        threshold = outliers.get("threshold", 1.5)

        df = remove_outliers(df, columns=columns, method=method, threshold=threshold)

    return df


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    cols_before = df_before.drop(columns=["id"], errors="ignore")
    cols_after= df_after.drop(columns=["id"], errors="ignore")
    report = {
        "rows_before": len(df_before),
        "rows_after": len(df_after),
        "rows_removed": len(df_before) - len(df_after),
        "columns_before": len(cols_before.columns),
        "columns_after": len(cols_after.columns),
        "columns_removed": len(cols_before.columns) - len(cols_after.columns)
    }
    return report