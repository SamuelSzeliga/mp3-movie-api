import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src._init_ import DatasetInfo, HealthResponse, setup_logging, ProcessConfig, ProcessingReport, log_requests
from src._init_ import MovieStorage, MovieUploadInfo, MovieDataResponse, MovieProcessingReport
from src.storage import MOVIE_COLUMNS
from data_pipeline._init_ import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = MovieStorage()
app.middleware("http")(log_requests)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version":"1.0.0"}


@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):

    if Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Non-CSV file uploaded")
    
    contents = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning(f"Cannot read CSV: {error}")
        raise HTTPException(status_code=400, detail="Cannot read the uploaded CSV")
    
    if list(df.columns) != MOVIE_COLUMNS:
        raise HTTPException(status_code=400, detail=f"CSV must have {MOVIE_COLUMNS}")
   
    if df.empty:
        raise HTTPException(status_code=400, detail="CSV must have at least one data row")

    df = df[MOVIE_COLUMNS]

    storage.save(df)
    logger.info(f"Filename: {file.filename}, row count: {len(df)}")

    return MovieUploadInfo(filename=file.filename, rows=len(df), columns=len(MOVIE_COLUMNS), column_names=MOVIE_COLUMNS)


@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
  
    df = storage.get()
    if df is None or df.empty:
        logger.info(f"No movies stored")
        return {"Data": [],
                "total_rows": 0}

    records = df.head(limit).to_dict(orient="records")
    logger.info(f"Retrieved {len(records)} movies, total number: {len(df)})")

    return {"data": records,
            "total_rows": len(df)}


@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):
    try:
        result = storage.query_movies(columns, min_rating, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    logger.info(
        f"Selected columns={columns}, min_rating={min_rating}"
        f"Returned {len(result)} rows"
    )
    return result


@app.post("/datasets/{dataset_id}/process", response_model=ProcessingReport)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    
    #Retrieve copy
    df = storage.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Does not exist")

    #Convert to dictionary
    config_dictionary = config.model_dump()

    #Confirm numeric columns exist in df
    missing_cols = [col for col in config.validation.required_columns if col not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_cols)}")

    #Validate using configured required and numeric columns
    try:
        validated_df = validate_dataframe(df, required_columns=config.validation.required_columns, numeric_columns=config.validation.numeric_columns)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    #Record how many rows removed and copy validated DataFrame before processing
    validation_rows_removed = len(df) - len(validated_df)
    validated_copy = validated_df.copy()
    logger.info(f"Validation removed {validation_rows_removed} rows")

    #Process data with validated DataFrame and full configuration dictionary
    try:
        processed_df = process_data(validated_copy, config_dictionary)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    #Cleaning report
    cleaning_report = create_cleaning_report(df_before=validated_df, df_after=processed_df)

    #Update after validation and processing both succeed
    storage.update(dataset_id, processed_df)
    
    #Return dict matching ProcessingReport
    return {
        "id": dataset_id,
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report
    }


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
   
    df = storage.get()
    if df is None:
        raise HTTPException(status_code=400, detail="DataFrame is empty")
    
    config_dictionary = config.model_dump()

    #Confirm numeric columns exist in df
    missing_cols = [col for col in config.validation.required_columns if col not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_cols)}")

    #Validate using configured required and numeric columns
    try:
        validated_df = validate_dataframe(df, required_columns=config.validation.required_columns, numeric_columns=config.validation.numeric_columns)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    #Record how many rows removed and copy validated DataFrame before processing
    validation_rows_removed = len(df) - len(validated_df)
    validated_copy = validated_df.copy()
    logger.info(f"Validation removed {validation_rows_removed} rows")

    #Process data with validated DataFrame and full configuration dictionary
    try:
        processed_df = process_data(validated_copy, config_dictionary)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    #Cleaning report
    cleaning_report = create_cleaning_report(df_before=validated_df, df_after=processed_df)

    storage.save(processed_df)
    return {
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report
    }