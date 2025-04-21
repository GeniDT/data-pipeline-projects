import pandas as pd
import matplotlib.pyplot as plt

# 1. Revenue vs. Budget Trends
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


# 3. Popularity vs. Rating
def plot_popularity_vs_rating(df):
    plt.scatter(df['popularity'], df['vote_average'])
    plt.title('Popularity vs. Rating')
    plt.xlabel('Popularity')
    plt.ylabel('Rating')
    plt.show()

# 4. Yearly Trends in Box Office Performance
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


# 5. Comparison of Franchise vs. Standalone Success
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
