import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DatasetStorage:
    def __init__(self):
        self._store = {}
        self._counter = 0


    def save(self, df, filename):
        """Store a copy of the data and return a new integer ID."""
        self._counter += 1
        dataset_id = self._counter 
        self._store[dataset_id] = {"filename": filename, "data": df.copy()}
        
        logger.debug(f"Stored dataset: id={dataset_id}, rows={len(df)}")
        return dataset_id


    def get(self, dataset_id):
        """Return a copy of the stored DataFrame, or None."""
        item = self._store.get(dataset_id)
        if item is None:
            return None
        logger.debug(f"Retrieved dataset copy: id={dataset_id}, rows={len(item["data"])}")
        return item["data"].copy()


    def get_metadata(self, dataset_id):
        """Return the dataset metadata, or None."""
        item = self._store.get(dataset_id)
        if item is None:
            return None

        df = item["data"]
        metadata = {
            "id": dataset_id,
            "filename": item["filename"],
            "rows" : len(df),
            "columns" : len(df.columns),
            "column_names" : list(df.columns)
        }
        logger.debug(f"Retrieved metadata: filename={item["filename"]}, id={dataset_id}, rows={len(df)}, columns={len(df.columns)}")
        return metadata


    def update(self, dataset_id, df):
        """Replace an existing dataset; return True, or False if missing."""
        if dataset_id not in self._store:
            logger.debug(f"src/update: False")
            return False
        
        self._store[dataset_id]["data"] = df.copy()
        logger.debug(f"src/update: True")
        return True
    

    def clear(self):
        """Clear all data and reset the ID counter."""
        self._store.clear()
        self._counter = 0