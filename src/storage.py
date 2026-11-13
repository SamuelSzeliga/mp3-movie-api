import logging
import sqlite3
import pandas as pd
from .database import get_connection, initialize_database

logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]

class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)


    def save(self, df):
        """Replace all movie rows in one transaction."""

        connection = get_connection(self.db_path)
        try:
            df = df.replace({pd.NA: None, float('nan'): None})
            connection.execute("DELETE FROM movie")
            
            sql_statement = "INSERT INTO movie (title, release_year, rating, genre) VALUES (?, ?, ?, ?)"
            movie = df[MOVIE_COLUMNS].values.tolist()
            connection.executemany(sql_statement, movie)

            connection.commit()
            logger.debug(f"Stored movies: rows = {len(movie)}")
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close


    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""

        connection = get_connection(self.db_path)
        try:
            cursor = connection.execute("SELECT title, release_year, rating, genre FROM movie ORDER BY id")
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=MOVIE_COLUMNS)
        finally:
            connection.close()


    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""

        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")
        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")
            
        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)

        try:
            cursor = connection.execute(
                f"SELECT {selected_columns} FROM movie ORDER BY id LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.debug(f"Selected columns: {selected_columns}, row count: {len(result)}")
            return result
        finally:
            connection.close()

        
    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        connection = get_connection(self.db_path)
        try:
            cursor = connection.execute("SELECT COUNT (*) FROM movie")
            return cursor.fetchone()[0]
        finally:
            connection.close()


    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""

        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")
    
        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Column does not exist: {column}")
                raise ValueError(f"Column does not exist: {column}")

        if "id" in MOVIE_COLUMNS: 
            selected_columns = ", ".join(["id"] + columns)
        else:
            selected_columns = ", ".join(columns)
    
        connection = get_connection(self.db_path)

        try:
            cursor = connection.execute(f" SELECT {selected_columns} FROM movie WHERE rating >= ? ORDER BY rating DESC, id ASC LIMIT ?", (min_rating, limit))
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            logger.debug(f"Selected columns: {selected_columns}, row count: {len(result)}")
            return result
        finally:
            connection.close()