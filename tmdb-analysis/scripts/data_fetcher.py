"""
data_fetcher.py
Functions for fetching TMDB data for analysis.
"""


import pandas as pd
import requests

def fetch_tmdb_data(movie_ids, api_key, base_url="https://api.themoviedb.org/3/movie/"):
    """Fetch movie data from TMDB API given a list of IDs."""
    all_data = []
    for movie_id in movie_ids:
        url = f"{base_url}{movie_id}?api_key={api_key}&append_to_response=credits"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            all_data.append(data)
        else:
            print(f"Failed to fetch movie with ID: {movie_id}")
    return pd.DataFrame(all_data)
