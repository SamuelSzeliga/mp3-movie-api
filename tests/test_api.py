import pytest

from src._init_ import MovieStorage
import main


def test_movies_persist(client, test_storage, uploaded_movies):

    #Make sure that data actually persisted in SQLite
    storage = MovieStorage(db_path= test_storage.db_path)

    df = storage.get()
    original_titles = ["Movie A", "Movie B", "Movie B", "Movie C", "Movie D",
                    "Movie D", "Movie E", "Movie F", "Movie G", "Movie H", 
                    "Movie I", "Movie J", "Movie K", "Movie L", "Movie M",
                    "Movie N", "Movie O", "Movie P", "Movie Q", "Movie R", ]

    assert len(df) == 20
    assert storage.count_movies() == 20
    assert list(df.columns[1:]) == ["title", "release_year", "rating", "genre"]
    assert df["title"].tolist() == original_titles

    stored_movies = storage.select_columns(["title"], limit=100)
    stored_ids = [movie["id"] for movie in stored_movies]

    response = client.get("/movies?limit=100")
    response_ids = [movie["id"] for movie in response.json()["data"]]

    assert stored_ids == list(range(1, 21))
    assert response_ids == stored_ids


def test_cache_and_processing(client, uploaded_movies, processing_body):

    response_lim_100 = client.get("/movies?limit=100")
    assert response_lim_100.status_code == 200
    assert main.cache.get(100) == response_lim_100.json()

    response_lim_1 = client.get("/movies?limit=1")
    assert response_lim_1.status_code == 200
    assert main.cache.get(1) == response_lim_1.json()

    repeat_response = client.get("/movies?limit=100")
    assert repeat_response.status_code == 200
    assert repeat_response.json() == response_lim_100.json()
    assert main.cache.get(100) == response_lim_100.json()

    processing_response = client.post("/movies/process", json=processing_body)
    assert processing_response.status_code == 200

    report = processing_response.json()
    assert report["validation_rows_removed"] == 0
    assert report["cleaning_report"] == {
        "rows_before": 20,
        "rows_after": 16,
        "rows_removed": 4,
        "columns_before": 4,
        "columns_after": 4,
        "columns_removed": 0}
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None

    retrieve_again = client.get("/movies?limit=100")
    assert retrieve_again.status_code == 200

    result = retrieve_again.json()
    assert result["total_rows"] == 16

    expected_titles = ["Movie A", "Movie B", "Movie C", "Movie D", "Movie E",
                    "Movie F", "Movie G", "Movie H", "Movie I", "Movie J",
                    "Movie K", "Movie L", "Movie M", "Movie N", "Movie O",
                    "Movie P"]
    actual_titles = [movie["title"] for movie in result["data"]]
    assert actual_titles == expected_titles

    actual_ids = [movie["id"] for movie in result["data"]]
    assert actual_ids == list(range(1, 17))
    assert main.cache.get(100) == result


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):

    first_response = client.get("/movies?limit=100")
    first_body = first_response.json()
    assert first_response.status_code == 200
    assert main.cache.get(100) == first_body

    def fail_if_called(*args, **kwargs):
        pytest.fail("Database method was called despite cache hit")
    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)

    second_response = client.get("/movies?limit=100")
    assert second_response.status_code == 200
    assert second_response.json() == first_body

