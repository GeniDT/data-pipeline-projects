import pandas as pd
import numpy as np
import json

#        DATA CLEANING UTILS

def parse_credits_column(df):
    """
    Parses the 'credits' column from a JSON string to a dictionary.
    """
    df['credits'] = df['credits'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    return df


def extract_cast_crew_info(credits_dict):
    """
    Extracts cast (first 5 actors), cast size, director, and crew size from the credits dictionary.
    """
    if not isinstance(credits_dict, dict):
        return pd.Series([None, None, None, None], index=['cast', 'cast_size', 'director', 'crew_size'])

    cast_list = credits_dict.get('cast', [])
    crew_list = credits_dict.get('crew', [])

    cast_names = [member['name'] for member in cast_list[:5] if 'name' in member]
    directors = [member['name'] for member in crew_list if member.get('job') == 'Director']

    return pd.Series([
        '|'.join(cast_names),
        len(cast_list),
        directors[0] if directors else None,
        len(crew_list)
    ], index=['cast', 'cast_size', 'director', 'crew_size'])


def drop_irrelevant_columns(df, cols_to_drop):
    """
    Drops irrelevant columns from the DataFrame.
    """
    return df.drop(columns=cols_to_drop)


def extract_collection_name(df):
    """
    Extracts collection name from 'belongs_to_collection' JSON column.
    """
    df['belongs_to_collection'] = df['belongs_to_collection'].apply(
        lambda x: x['name'] if isinstance(x, dict) else None
    )
    return df


def extract_genre_names(df):
    """
    Extracts genre names from 'genres' JSON column.
    """
    df['genres'] = df['genres'].apply(
        lambda genres: '|'.join([genre['name'] for genre in genres if 'name' in genre])
        if isinstance(genres, list) else None
    )
    return df


def extract_spoken_languages(df):
    """
    Extracts spoken languages from 'spoken_languages' JSON column.
    """
    df['spoken_languages'] = df['spoken_languages'].apply(
         lambda langs: '|'.join([lang['english_name'] for lang in langs if 'english_name' in lang])
        if isinstance(langs, list) else None
    )
    return df


def extract_production_countries(df):
    """
    Extracts production countries from 'production_countries' JSON column.
    """
    df['production_countries'] = df['production_countries'].apply(
        lambda countries: '|'.join([country['name'] for country in countries if 'name' in country])
        if isinstance(countries, list) else None
    )
    return df


def extract_production_companies(df):
    """
    Extracts production companies from 'production_companies' JSON column.
    """
    df['production_companies'] = df['production_companies'].apply(
        lambda companies: '|'.join([company['name'] for company in companies if 'name' in company])
        if isinstance(companies, list) else None
    )
    return df


def extract_all_fields(df):
    """
    Applies all extraction functions to the appropriate JSON columns.
    """
    df = extract_collection_name(df)
    df = extract_genre_names(df)
    df = extract_spoken_languages(df)
    df = extract_production_countries(df)
    df = extract_production_companies(df)
    return df


# ---------- Handling Missing & Incorrect Data ----------

def convert_column_datatypes(df):
    """
    Converts specific columns to numeric or datetime types.
    """
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce')
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')
    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce')
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce')
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    return df


def replace_unrealistic_values(df):
    """
    Replaces unrealistic values (like 0 in budget/revenue/runtime) with NaN.
    """
    df['budget'].replace(0, np.nan, inplace=True)
    df['revenue'].replace(0, np.nan, inplace=True)
    df['runtime'].replace(0, np.nan, inplace=True)
    return df


def convert_to_million(df):
    """
    Converts budget and revenue to millions of USD.
    """
    df['budget_musd'] = df['budget'] / 1_000_000
    df['revenue_musd'] = df['revenue'] / 1_000_000
    return df


def adjust_vote_average_by_genre(df):
    """
    Adjusts vote_average for movies with vote_count == 0
    by assigning the average vote_average for their genre.
    """
    df = df.copy()

    # Ensure genres are lists (if they were stored as strings)
    df['genres'] = df['genres'].apply(
        lambda x: x.split('|') if isinstance(x, str) else x
    )

    rated_movies = df[df['vote_count'] > 0].explode('genres')
    genre_avg_votes = (
        rated_movies.groupby('genres')['vote_average']
        .mean()
        .reset_index()
        .rename(columns={'vote_average': 'genre_vote_avg'})
    )

    df_exploded = df.explode('genres')
    df_exploded = df_exploded.merge(genre_avg_votes, on='genres', how='left')
    df_exploded['vote_average'] = np.where(
        df_exploded['vote_count'] == 0,
        df_exploded['genre_vote_avg'],
        df_exploded['vote_average']
    )

    df_updated = df_exploded.groupby('id', as_index=False).first()
    df_updated.drop(columns=['genre_vote_avg'], inplace=True)
    return df_updated


def replace_placeholders(df):
    """
    Replaces generic placeholder text in overview and tagline columns with NaN.
    """
    df = df.copy()
    df['overview'] = df['overview'].replace(['No Data', 'No Data Available', 'No Data...'], np.nan)
    df['tagline'] = df['tagline'].replace(['No Tagline', 'No Tagline Available', 'No Data...'], np.nan)
    return df


def drop_duplicates_and_missing_ids_titles(df):
    """
    Drops duplicate rows using only hashable columns 
    and removes rows with missing 'id' or 'title'.
    """
    # Keep only columns where all values are hashable (i.e., not lists or dicts)
    hashable_cols = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, (list, dict))).any()]
    
    # Drop duplicates only based on hashable columns
    df = df.drop_duplicates(subset=hashable_cols)

    # Drop rows with missing 'id' or 'title'
    df = df.dropna(subset=['id', 'title'])

    return df


def drop_sparse_rows(df, min_non_null=10):
    """
    Drops rows that have fewer than `min_non_null` non-null values.
    """
    return df[df.notnull().sum(axis=1) >= min_non_null]


def filter_released_movies(df):
    """
    Filters only movies with status 'Released' and drops the 'status' column.
    """
    df = df[df['status'] == 'Released']
    df = df.drop(columns=['status'], errors='ignore')
    return df


def reorder_columns(df):
    """
    Reorders DataFrame columns according to the required final structure.
    """
    ordered_columns = [
        'id', 'title', 'tagline', 'release_date', 'genres', 'belongs_to_collection',
        'original_language', 'budget_musd', 'revenue_musd', 'production_companies',
        'production_countries', 'vote_count', 'vote_average', 'popularity', 'runtime',
        'overview', 'spoken_languages', 'poster_path', 'cast', 'cast_size', 'director', 'crew_size'
    ]
    # Keep only existing columns (in case some are missing)
    ordered_columns = [col for col in ordered_columns if col in df.columns]
    return df[ordered_columns]


def reset_dataframe_index(df):
    """
    Resets the index of the DataFrame.
    """
    return df.reset_index(drop=True)