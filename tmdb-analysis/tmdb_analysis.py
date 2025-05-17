## THE MOVIE DATA ANALYSIS PIPELINE
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import json
import requests
import matplotlib.pyplot as plt

#        DATA EXTRACTION UTILS

"""
data_fetcher.py
Functions for fetching TMDB data for analysis.
"""

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


#        DATA CLEANING AND PREPROCESSING UTILS

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



#         KPI Implementation & Analysis

# Calculate Profit 
def calculate_profit(row):
    """
    Calculate profit as Revenue - Budget for each movie.
    :param row: DataFrame row containing movie data
    :return: Profit (Revenue - Budget)
    """
    return row['revenue_musd'] - row['budget_musd']

# Calculate ROI 
def calculate_roi(row):
    """
    Calculate ROI as Revenue / Budget (only for Budget ≥ 10M).
    :param row: DataFrame row containing movie data
    :return: ROI if Budget ≥ 10M, else None
    """
    return row['revenue_musd'] / row['budget_musd'] if row['budget_musd'] >= 10_000_000 else None

# KPI Rankings 
def kpi_ranking(df):
    """
    Rank movies based on various KPIs (Revenue, Budget, Profit, ROI, etc.).
    :param df: DataFrame containing movie data
    :return: Dictionary with top-ranked movies based on different KPIs
    """
    # Calculate Profit and ROI
    df['profit'] = df.apply(calculate_profit, axis=1)
    df['roi'] = df.apply(calculate_roi, axis=1)
    
    # Filter movies with Budget ≥ 10M for ROI ranking
    filtered_df = df[df['budget_musd'] >= 10_000_000]

    rankings = {
        "Highest Revenue": df.sort_values(by='revenue_musd', ascending=False).head(1),
        "Highest Budget": df.sort_values(by='budget_musd', ascending=False).head(1),
        "Highest Profit": df.sort_values(by='profit', ascending=False).head(1),
        "Lowest Profit": df.sort_values(by='profit').head(1),
        "Highest ROI": filtered_df.sort_values(by='roi', ascending=False).head(1),
        "Lowest ROI": filtered_df.sort_values(by='roi').head(1),
        "Most Voted": df.sort_values(by='vote_count', ascending=False).head(1),
        "Highest Rated": df[df['vote_count'] >= 10].sort_values(by='vote_average', ascending=False).head(1),
        "Lowest Rated": df[df['vote_count'] >= 10].sort_values(by='vote_average').head(1),
        "Most Popular": df.sort_values(by='popularity', ascending=False).head(1)
    }
    
    return rankings

# Advanced Movie Filtering 
def filter_movies(df, genre=None, actor=None, director=None, min_votes=0, min_budget=0, sort_by=None):
    """
    Filter movies based on specific criteria: genre, actor, director, min_votes, min_budget, and sorting.
    """
    if genre:
        df = df[df['genres'].str.contains(genre, case=False, na=False)]
    if actor:
        df = df[df['cast'].str.contains(actor, case=False, na=False)]
    if director:
        df = df[df['director'].str.contains(director, case=False, na=False)]
    if min_votes > 0:
        df = df[df['vote_count'] >= min_votes]
    if min_budget > 0:
        df = df[df['budget_musd'] >= min_budget]
    if sort_by:
        df = df.sort_values(by=sort_by, ascending=False)
    
    return df

# Franchise vs Standalone Movie Comparison
def franchise_vs_standalone(df):
    """
    Compare franchise vs standalone movies in terms of:
    - Mean Revenue, Median ROI, Mean Budget, Mean Popularity, Mean Rating.
    :param df: DataFrame containing movie data
    :return: Tuple with statistics for franchise and standalone movies
    """
    franchise_movies = df[df['belongs_to_collection'].notna()]
    standalone_movies = df[df['belongs_to_collection'].isna()]
    
    franchise_stats = {
        'Mean Revenue': franchise_movies['revenue_musd'].mean(),
        'Median ROI': franchise_movies['roi'].median(),
        'Mean Budget': franchise_movies['budget_musd'].mean(),
        'Mean Popularity': franchise_movies['popularity'].mean(),
        'Mean Rating': franchise_movies['vote_average'].mean()
    }
    
    standalone_stats = {
        'Mean Revenue': standalone_movies['revenue_musd'].mean(),
        'Median ROI': standalone_movies['roi'].median(),
        'Mean Budget': standalone_movies['budget_musd'].mean(),
        'Mean Popularity': standalone_movies['popularity'].mean(),
        'Mean Rating': standalone_movies['vote_average'].mean()
    }
    
    return franchise_stats, standalone_stats

# Most Successful Franchises
def most_successful_franchises(df):
    """
    Find the most successful movie franchises based on:
    - Total number of movies in franchise
    - Total & Mean Budget
    - Total & Mean Revenue
    - Mean Rating
    :param df: DataFrame containing movie data
    :return: DataFrame with franchise performance stats
    """
    franchises = df[df['belongs_to_collection'].notna()]
    
    franchise_groups = franchises.groupby('belongs_to_collection').agg(
        movie_count=('id', 'count'),
        total_budget=('budget_musd', 'sum'),
        mean_budget=('budget_musd', 'mean'),
        total_revenue=('revenue_musd', 'sum'),
        mean_revenue=('revenue_musd', 'mean'),
        mean_rating=('vote_average', 'mean')
    )
    
    return franchise_groups.sort_values(by='movie_count', ascending=False)

# Most Successful Directors
def most_successful_directors(df):
    """
    Find the most successful directors based on:
    - Total Number of Movies Directed
    - Total Revenue
    - Mean Rating
    :param df: DataFrame containing movie data
    :return: DataFrame with director performance stats
    """
    directors = df.groupby('director').agg(
        movie_count=('id', 'count'),
        total_revenue=('revenue_musd', 'sum'),
        mean_rating=('vote_average', 'mean')
    )
    
    return directors.sort_values(by='movie_count', ascending=False)



#         Data Visualization 

# Revenue vs. Budget Trends
def plot_revenue_vs_budget(df):
    """
    Plots Revenue vs Budget using converted million USD columns.
    """
    if 'budget_musd' not in df.columns or 'revenue_musd' not in df.columns:
        raise ValueError("Required columns 'budget_musd' and/or 'revenue_musd' not found in DataFrame.")

    plt.figure(figsize=(10, 6))
    plt.scatter(df['budget_musd'], df['revenue_musd'], alpha=0.6, color='teal')
    plt.title('Revenue vs. Budget Trends')
    plt.xlabel('Budget (Million USD)')
    plt.ylabel('Revenue (Million USD)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def plot_roi_distribution_by_genre(df):
    df = df.copy()

    # Filter out invalid rows (can't divide by zero)
    df = df[(df['budget_musd'] > 0) & (df['revenue_musd'] > 0)]

    # Calculate ROI
    df['roi'] = df['revenue_musd'] / df['budget_musd']

    # Group by genre and get average ROI
    genre_roi = df.groupby('genres')['roi'].mean().sort_values(ascending=False)

    # Plot
    genre_roi.plot(kind='bar', color='teal')
    plt.title('Average ROI by Genre')
    plt.xlabel('Genre')
    plt.ylabel('ROI')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# Popularity vs. Rating
def plot_popularity_vs_rating(df):
    plt.scatter(df['popularity'], df['vote_average'])
    plt.title('Popularity vs. Rating')
    plt.xlabel('Popularity')
    plt.ylabel('Rating')
    plt.show()

# Yearly Trends in Box Office Performance
def plot_yearly_trends(df):
    # Make sure release_date is datetime and extract year
    df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year

    # Group by year with the correct column names
    yearly_trends = df.groupby('year').agg(
        total_revenue=('revenue_musd', 'sum'),
        mean_rating=('vote_average', 'mean')
    )

    # Plot
    yearly_trends.plot(kind='line', figsize=(10, 6))
    plt.title('Yearly Trends in Box Office Performance')
    plt.xlabel('Year')
    plt.ylabel('Total Revenue (in millions)')
    plt.grid(True)
    plt.show()


# Comparison of Franchise vs. Standalone Success
def plot_franchise_vs_standalone(df):
    franchise_stats, standalone_stats = franchise_vs_standalone(df)
    
    # Plot revenue comparison between franchise and standalone
    labels = ['Franchise', 'Standalone']
    revenue = [franchise_stats['Mean Revenue'], standalone_stats['Mean Revenue']]
    plt.bar(labels, revenue, color=['orange', 'green'])
    plt.title('Franchise vs. Standalone Revenue Comparison')
    plt.ylabel('Mean Revenue (in millions)')
    plt.show()

# Helper function to calculate stats for franchise vs standalone
def franchise_vs_standalone(df):
    franchise_movies = df[df['is_franchise'] == 1]
    standalone_movies = df[df['is_franchise'] == 0]

    franchise_stats = {
        'Mean Revenue': franchise_movies['revenue_musd'].mean(),
        'Mean Rating': franchise_movies['vote_average'].mean(),
        'Total Movies': franchise_movies.shape[0]
    }

    standalone_stats = {
        'Mean Revenue': standalone_movies['revenue_musd'].mean(),
        'Mean Rating': standalone_movies['vote_average'].mean(),
        'Total Movies': standalone_movies.shape[0]
    }

    return franchise_stats, standalone_stats


    return franchise_stats, standalone_stats

def add_franchise_flag(df):
    df['is_franchise'] = df['belongs_to_collection'].notnull().astype(int)
    return df