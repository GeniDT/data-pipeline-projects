import pandas as pd

# 1. **Calculate Profit** - Helper Function
def calculate_profit(row):
    """
    Calculate profit as Revenue - Budget for each movie.
    :param row: DataFrame row containing movie data
    :return: Profit (Revenue - Budget)
    """
    return row['revenue_musd'] - row['budget_musd']

# 2. **Calculate ROI** - Helper Function
def calculate_roi(row):
    """
    Calculate ROI as Revenue / Budget (only for Budget ≥ 10M).
    :param row: DataFrame row containing movie data
    :return: ROI if Budget ≥ 10M, else None
    """
    return row['revenue_musd'] / row['budget_musd'] if row['budget_musd'] >= 10_000_000 else None

# 3. **KPI Rankings** - Helper Function
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

# 4. **Advanced Movie Filtering** - Helper Function
def filter_movies(df, genre=None, actor=None, director=None, min_votes=0, min_budget=0, sort_by=None):
    """
    Filter movies based on specific criteria: genre, actor, director, min_votes, min_budget, and sorting.
    :param df: DataFrame containing movie data
    :param genre: Genre filter (optional)
    :param actor: Actor filter (optional)
    :param director: Director filter (optional)
    :param min_votes: Minimum vote count filter (optional)
    :param min_budget: Minimum budget filter (optional)
    :param sort_by: Sorting column (optional)
    :return: Filtered DataFrame based on criteria
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

# 5. **Franchise vs Standalone Movie Comparison** - Helper Function
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

# 6. **Most Successful Franchises** - Helper Function
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

# 7. **Most Successful Directors** - Helper Function
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