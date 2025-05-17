# TMDB Movie Data Analysis

## Overview
This project analyzes movie data fetched from The Movie Database (TMDB) API. It involves data extraction, cleaning, preprocessing, key performance indicator (KPI) implementation, and visualization to gain insights into movie trends, franchises, directors, and various metrics like revenue, budget, and ratings.

## Project Structure
The analysis is divided into four main steps:

1. **Data Fetching**: Retrieves raw movie data from the TMDB API
2. **Data Cleaning**: Processes and prepares the data for analysis
3. **KPI Implementation**: Calculates and analyzes key metrics
4. **Data Visualization**: Creates visual representations of the findings

## Key Features
- Fetches data for specific movie IDs from TMDB API
- Cleans and preprocesses data including:
  - JSON column parsing
  - Irrelevant column removal
  - Data type conversion
  - Value normalization
  - Missing data handling
- Calculates important KPIs:
  - Profit and ROI calculations
  - Franchise vs standalone movie comparisons
  - Director and genre analyses
- Generates visualizations:
  - Revenue vs budget trends
  - ROI distribution by genre
  - Popularity vs rating comparisons
  - Yearly trends
  - Franchise performance

## Data Sources
- The Movie Database (TMDB) API
- Sample movie IDs used: [0, 299534, 19995, 140607, 299536, 597, 135397, 420818, 24428, 168259, 99861, 284054, 12445, 181808, 330457, 351286, 109445, 321612, 260513]

## Technical Details
- Python
- Key libraries:
  - pandas for data manipulation
  - matplotlib for visualization
  - Custom modules for data fetching and cleaning
- Jupyter Notebook environment

## Usage
1. Clone the repository
2. Install required dependencies
3. Run the Jupyter notebook `analysis.ipynb`
4. Follow the step-by-step analysis process
5. Replace API section with your genrated API key.

## Results
The analysis provides insights into:
- Most profitable movies and franchises
- Highest rated and most popular movies
- Budget vs revenue relationships
- Genre performance metrics
- Director success metrics
