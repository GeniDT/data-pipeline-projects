"""
Python for containing functions for pipeline process
utils.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    when,
    lit,
    to_date,
    udf,
    sum as spark_sum,
    desc,
    asc,
    round,
    split,
    explode,
    regexp_replace,
    trim,
    count,
    avg as spark_avg,
    monotonically_increasing_id,
    collect_list,
    concat_ws,
    from_json,
    substring
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    ArrayType,
    BooleanType,
    DoubleType,
    LongType,
    DateType,
)
from dotenv import load_dotenv
import os
import requests
import json
import time

# Load environment variables from .env file
load_dotenv()

import pandas as pd
import requests
import json
import os
from pyspark.sql import SparkSession

# Cache file to store raw data
CACHE_FILE = "raw_data_cache.json"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3/movie/"

# Initialize Spark session
spark = SparkSession.builder.appName("TMDB Data").getOrCreate()

def extract_tmdb_data(movie_ids, api_key=TMDB_API_KEY, base_url=BASE_URL):
    """
    Fetches movie data from TMDB API for a given list of movie IDs, caches the data,
    and returns the data as a PySpark DataFrame.
    
    Args:
        movie_ids (list): List of movie IDs to fetch.
        api_key (str, optional): The TMDB API key. Defaults to the TMDB_API_KEY environment variable.
        base_url (str, optional): The base URL for the TMDB API.

    Returns:
        pyspark.sql.DataFrame: PySpark DataFrame containing the movie data.
    """
    all_data = []

    for movie_id in movie_ids:
        url = f"{base_url}{movie_id}?api_key={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad status codes (4xx or 5xx)
            raw_data = response.json()

            # Cache the data upon successful retrieval
            try:
                with open(CACHE_FILE, "r") as f:
                    cached_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                cached_data = {}  # Initialize cache if file not found or invalid JSON

            cached_data[movie_id] = raw_data  # Update/add to cache
            with open(CACHE_FILE, "w") as f:
                json.dump(cached_data, f, indent=2)  # Pretty print json

            all_data.append(raw_data)  # Add the fetched data to the list

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for movie ID {movie_id}: {e}")
            if response is not None and response.status_code == 404:
                print(f"Movie ID {movie_id} not found. Skipping.")
            continue  # Skip this movie_id and move to the next one

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response for movie ID {movie_id}: {e}")
            if response is not None:
                print(f"Raw response content: {response.text}")  # Print raw content for debugging
            continue  # Skip this movie_id and move to the next one

        except Exception as e:
            print(f"An unexpected error occurred for movie ID {movie_id}: {e}")
            continue  # Skip this movie_id and move to the next one

    # Convert the list of data into a Pandas DataFrame
    movie_data_df = pd.DataFrame(all_data)

    # Convert the Pandas DataFrame into a PySpark DataFrame
    movie_data_spark_df = spark.createDataFrame(movie_data_df)

    return movie_data_spark_df


def extract_movie_data(spark, movie_ids):
    """
    Orchestrates the extraction of movie data from TMDB for a list of movie IDs using pure PySpark.

    Args:
        spark (SparkSession): The SparkSession.
        movie_ids (list): A list of movie IDs to extract.

    Returns:
        pyspark.sql.DataFrame: A DataFrame containing the extracted movie data, or an empty DataFrame on error.
    """
    # Load API key from environment variable
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise ValueError("TMDB_API_KEY environment variable not set.")

    # Filter out invalid movie IDs (e.g., 0)
    valid_movie_ids = [mid for mid in movie_ids if mid != 0]

    # Define the schema
    schema = StructType(
        [
            StructField("adult", BooleanType(), True),
            StructField("budget", IntegerType(), True),
            StructField(
                "genres",
                ArrayType(
                    StructType(
                        [
                            StructField("id", IntegerType(), True),
                            StructField("name", StringType(), True),
                        ]
                    ),
                    True,
                ),
                True,
            ),
            StructField("id", IntegerType(), True),
            StructField("original_language", StringType(), True),
            StructField("original_title", StringType(), True),
            StructField("overview", StringType(), True),
            StructField("popularity", DoubleType(), True),
            StructField("poster_path", StringType(), True),
            StructField("release_date", StringType(), True),
            StructField("revenue", LongType(), True),
            StructField("runtime", IntegerType(), True),
            StructField("status", StringType(), True),
            StructField("tagline", StringType(), True),
            StructField("title", StringType(), True),
            StructField("video", BooleanType(), True),
            StructField("vote_average", DoubleType(), True),
            StructField("vote_count", IntegerType(), True),
            StructField("belongs_to_collection", StringType(), True),
            StructField("production_companies", StringType(), True),
            StructField("production_countries", StringType(), True),
            StructField("spoken_languages", StringType(), True)
        ]
    )

    # Create an RDD of movie IDs
    movie_ids_rdd = spark.sparkContext.parallelize(valid_movie_ids)

    # Fetch data for each movie ID using map, filtering out None results
    movie_data_rdd = (
        movie_ids_rdd.map(lambda movie_id: (movie_id, extract_tmdb_data(movie_id, api_key)))
        .filter(lambda x: x[1] is not None)
        .map(lambda x: (x[0], json.dumps(x[1])))  # Convert the dictionary to a JSON string
    )

    # Create DataFrame from the RDD of JSON strings, with the schema
    movie_data_df = spark.read.json(movie_data_rdd.values(), schema=schema)

    # Clean the data (handling potential encoding issues)
    movie_data_df = (
        movie_data_df.withColumn("overview", substring(col("overview"), 1, 100))
        .withColumn("title", regexp_replace(col("title"), "[^\\x00-\\x7F]+", ""))
    )

    return movie_data_df


from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, MapType

from pyspark.sql.functions import col, explode, to_json
from pyspark.sql.types import MapType, ArrayType, StructType

from pyspark.sql.functions import col, explode, to_json
from pyspark.sql.types import MapType, ArrayType, StructType

from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, MapType, StructType

def flatten_df(df):
    # List to store flattened columns
    flat_columns = []
    
    # Loop through all columns to identify and flatten any nested structures
    for col_name, col_type in df.dtypes:
        if isinstance(col_type, ArrayType):  # If the column is an array, use explode
            flat_columns.append(
                F.explode(F.col(col_name)).alias(col_name)
            )
        elif isinstance(col_type, MapType):  # If the column is a map, handle key-value pairs
            # This loop will add each key-value pair as a separate column
            map_keys = df.select(F.col(col_name)).first()[0].keys()  # Get the map keys
            for key in map_keys:
                flat_columns.append(
                    F.col(f"{col_name}.{key}").alias(f"{col_name}_{key}")
                )
        elif isinstance(col_type, StructType):  # If it's a struct, access the fields directly
            for field in col_type.fields:
                flat_columns.append(
                    F.col(f"{col_name}.{field.name}").alias(f"{col_name}_{field.name}")
                )
        else:
            # Keep non-nested columns as is
            flat_columns.append(F.col(col_name))
    
    return df.select(flat_columns)


    


def clean_movie_data(movie_data_df):
    """
    Cleans and preprocesses the movie data DataFrame.

    Args:
        movie_data_df (pyspark.sql.DataFrame): The input DataFrame.

    Returns:
        pyspark.sql.DataFrame: The cleaned DataFrame.
    """
    # 1. Drop Irrelevant Columns
    drop_cols = ["adult", "imdb_id", "original_title", "video", "homepage"]
    movie_data_df = movie_data_df.drop(*drop_cols)

    # 2. Evaluate JSON-like Columns
    genre_schema = ArrayType(
        StructType([StructField("id", IntegerType()), StructField("name", StringType())])
    )

    movie_data_df = movie_data_df.withColumn(
        "genres_parsed", from_json(col("genres"), genre_schema)
    )

    movie_data_df = movie_data_df.withColumn(
        "genres_exploded", explode(col("genres_parsed"))
    )

    movie_data_df = movie_data_df.withColumn(
        "genre_names", col("genres_exploded.name")
    )
    movie_data_df = movie_data_df.groupBy(col("id")).agg(
        collect_list(col("genre_names")).alias("genre_names")
    )
    movie_data_df = movie_data_df.withColumn(
        "genres", concat_ws("|", col("genre_names"))
    )
    movie_data_df = movie_data_df.drop("genres_parsed").drop("genres_exploded").drop("genre_names")

    # Similar logic for other JSON-like columns, adapting the schema and extraction as needed.
    collection_schema = StructType([
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("poster_path", StringType()),
        StructField("backdrop_path", StringType()),
    ])
    movie_data_df = movie_data_df.withColumn(
        "belongs_to_collection_parsed", from_json(col("belongs_to_collection"), collection_schema)
    )

    movie_data_df = movie_data_df.withColumn(
        "belongs_to_collection_name", col("belongs_to_collection_parsed.name")
    )
    movie_data_df = movie_data_df.drop("belongs_to_collection_parsed").drop("belongs_to_collection")

    production_countries_schema = ArrayType(
        StructType([StructField("iso_3166_1", StringType()), StructField("name", StringType())])
    )
    movie_data_df = movie_data_df.withColumn(
        "production_countries_parsed", from_json(col("production_countries"), production_countries_schema)
    )
    movie_data_df = movie_data_df.withColumn(
        "production_countries_exploded", explode(col("production_countries_parsed"))
    )

    movie_data_df = movie_data_df.withColumn(
        "production_country_names", col("production_countries_exploded.name")
    )
    movie_data_df = movie_data_df.groupBy(col("id")).agg(
        collect_list(col("production_country_names")).alias("production_country_names")
    )
    movie_data_df = movie_data_df.withColumn("production_countries", concat_ws("|", col("production_country_names")))
    movie_data_df = movie_data_df.drop("production_countries_parsed").drop("production_countries_exploded").drop("production_country_names")
    production_companies_schema = ArrayType(
        StructType([StructField("name", StringType())])
    )
    movie_data_df = movie_data_df.withColumn(
        "production_companies_parsed", from_json(col("production_companies"), production_companies_schema)
    )
    movie_data_df = movie_data_df.withColumn(
        "production_companies_exploded", explode(col("production_companies_parsed"))
    )

    movie_data_df = movie_data_df.withColumn(
        "production_company_names", col("production_companies_exploded.name")
    )
    movie_data_df = movie_data_df.groupBy(col("id")).agg(
        collect_list(col("production_company_names")).alias("production_company_names")
    )
    movie_data_df = movie_data_df.withColumn("production_companies", concat_ws("|", col("production_company_names")))
    movie_data_df = movie_data_df.drop("production_companies_exploded").drop("production_company_names").drop("production_companies_parsed")

    spoken_languages_schema = ArrayType(
        StructType([StructField("iso_639_1", StringType()), StructField("name", StringType())])
    )
    movie_data_df = movie_data_df.withColumn(
        "spoken_languages_parsed", from_json(col("spoken_languages"), spoken_languages_schema)
    )
    movie_data_df = movie_data_df.withColumn(
        "spoken_languages_exploded", explode(col("spoken_languages_parsed"))
    )

    movie_data_df = movie_data_df.withColumn(
        "spoken_language_names", col("spoken_languages_exploded.name")
    )
    movie_data_df = movie_data_df.groupBy(col("id")).agg(
        collect_list(col("spoken_language_names")).alias("spoken_language_names")
    )
    movie_data_df = movie_data_df.withColumn("spoken_languages", concat_ws("|", col("spoken_language_names")))
    movie_data_df = movie_data_df.drop("spoken_languages_exploded").drop("spoken_language_names").drop("spoken_languages_parsed")

    # 4. Convert Column Datatypes and Replace Unrealistic Values:
    movie_data_df = movie_data_df.withColumn("budget", col("budget").cast(DoubleType()))
    movie_data_df = movie_data_df.withColumn("id", col("id").cast(DoubleType()))
    movie_data_df = movie_data_df.withColumn("popularity", col("popularity").cast(DoubleType()))
    movie_data_df = movie_data_df.withColumn(
        "release_date", to_date(col("release_date"), "yyyy-MM-dd")
    )

    movie_data_df = movie_data_df.withColumn(
        "budget",
        when(col("budget") == 0, F.lit(None)).otherwise(col("budget") / 1000000),  # in millions
    )
    movie_data_df = movie_data_df.withColumn(
        "revenue",
        when(col("revenue") == 0, F.lit(None)).otherwise(col("revenue") / 1000000),  # in millions
    )
    movie_data_df = movie_data_df.withColumn(
        "runtime", when(col("runtime") == 0, F.lit(None)).otherwise(col("runtime"))
    )
    movie_data_df = movie_data_df.withColumn(
        "overview", when(col("overview") == "No Data", F.lit(None)).otherwise(col("overview"))
    )
    movie_data_df = movie_data_df.withColumn(
        "tagline", when(col("tagline") == "No Data", F.lit(None)).otherwise(col("tagline"))
    )

    # 6. Remove Duplicates and Drop Rows:
    movie_data_df = movie_data_df.dropDuplicates()
    movie_data_df = movie_data_df.filter(col("id").isNotNull() & col("title").isNotNull())

    # 7. Keep Rows with Minimum Non-NaN Values:
    def count_non_nulls(*cols):
        return spark_sum(col(c).isNotNull().cast("integer") for c in cols)

    count_non_nulls_udf = udf(count_non_nulls, IntegerType())

    all_cols = movie_data_df.columns
    movie_data_df = movie_data_df.withColumn(
        "non_null_count", count_non_nulls_udf(*all_cols)
    )
    movie_data_df = movie_data_df.filter(col("non_null_count") >= 10).drop("non_null_count")

    # 8. Filter by 'Released' Status:
    movie_data_df = movie_data_df.filter(col("status") == "Released").drop("status")

    # 9. Reorder Columns:
    new_order = [
        "id",
        "title",
        "tagline",
        "release_date",
        "genres",
        "belongs_to_collection_name",
        "original_language",
        "budget",
        "revenue",
        "production_companies",
        "production_countries",
        "vote_count",
        "vote_average",
        "popularity",
        "runtime",
        "overview",
        "spoken_languages",
        "poster_path",
    ]  # Removed cast, cast_size, director, crew_size
    movie_data_df = movie_data_df.select(new_order)

    # 10. Reset Index:
    movie_data_df = movie_data_df.withColumn("index", monotonically_increasing_id())

    return movie_data_df


def analyze_movie_data(movie_data_df):
    """
    Analyzes the movie data DataFrame to generate KPIs.

    Args:
        movie_data_df (pyspark.sql.DataFrame): The input DataFrame.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    analysis_results = {}

    # 1. Identify Best/Worst Performing Movies:
    analysis_results["highest_revenue_movies"] = (
        movie_data_df.orderBy(desc("revenue")).limit(10).toPandas()
    )
    analysis_results["highest_budget_movies"] = (
        movie_data_df.orderBy(desc("budget")).limit(10).toPandas()
    )
    analysis_results["highest_profit_movies"] = (
        movie_data_df.withColumn("profit", col("revenue") - col("budget"))
        .orderBy(desc("profit"))
        .limit(10)
        .toPandas()
    )
    analysis_results["lowest_profit_movies"] = (
        movie_data_df.withColumn("profit", col("revenue") - col("budget"))
        .orderBy(asc("profit"))
        .limit(10)
        .toPandas()
    )
    analysis_results["highest_roi_movies"] = (
        movie_data_df.withColumn("roi", round((col("revenue") / col("budget")), 2))
        .filter(col("budget") >= 10)
        .orderBy(desc("roi"))
        .limit(10)
        .toPandas()
    )
    analysis_results["lowest_roi_movies"] = (
        movie_data_df.withColumn("roi", round((col("revenue") / col("budget")), 2))
        .filter(col("budget") >= 10)
        .orderBy(asc("roi"))
        .limit(10)
        .toPandas()
    )
    analysis_results["most_voted_movies"] = (
        movie_data_df.orderBy(desc("vote_count")).limit(10).toPandas()
    )
    analysis_results["highest_rated_movies"] = (
        movie_data_df.filter(col("vote_average") >= 10)
        .orderBy(desc("vote_average"))
        .limit(10)
        .toPandas()
    )
    analysis_results["lowest_rated_movies"] = (
        movie_data_df.filter(col("vote_average") >= 10)
        .orderBy(asc("vote_average"))
        .limit(10)
        .toPandas()
    )
    analysis_results["most_popular_movies"] = (
        movie_data_df.orderBy(desc("popularity")).limit(10).toPandas()
    )

    # 2. Advanced Movie Filtering & Search Queries:
    analysis_results["search1_df"] = (
        movie_data_df.filter(
            col("genres").like("%Science Fiction%") & col("genres").like("%Action%")
        )
        .filter(
            col("overview").like(
                "%Bruce Willis%"
            )
        )  # added a filter on the overview, since "starring" is not a column
        .orderBy(desc("vote_average"))
        .toPandas()
    )

    analysis_results["search2_df"] = (
        movie_data_df.filter(
            col("overview").like("%Uma Thurman%") & col("overview").like("%Quentin Tarantino%")
        )  # added filter on overview
        .orderBy(asc("runtime"))
        .toPandas()
    )

    # 3. Franchise vs. Standalone Movie Performance:
    analysis_results["franchise_performance_df"] = (
        movie_data_df.groupBy("belongs_to_collection_name")
        .agg(
            spark_avg("revenue").alias("mean_revenue"),
            spark_avg("budget").alias("mean_budget"),
            spark_avg("popularity").alias("mean_popularity"),
            spark_avg("vote_average").alias("mean_rating"),
        )
        .toPandas()
    )

    # 4. Most Successful Movie Franchises:
    analysis_results["franchise_success_df"] = (
        movie_data_df.groupBy("belongs_to_collection_name")
        .agg(
            count("*").alias("num_movies"),
            spark_sum("budget").alias("total_budget"),
            spark_avg("budget").alias("mean_budget"),
            spark_sum("revenue").alias("total_revenue"),
            spark_avg("revenue").alias("mean_revenue"),
            spark_avg("vote_average").alias("mean_rating"),
        )
        .orderBy(desc("total_revenue"))
        .toPandas()
    )
    return analysis_results


def visualize_movie_data(movie_data_df, analysis_results):
    """
    Visualizes the movie data using Pandas and Matplotlib.

    Args:
        movie_data_df (pyspark.sql.DataFrame): The input DataFrame.
        analysis_results (dict): A dictionary containing the analysis results.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    # 1. Revenue vs. Budget Trends
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=analysis_results["highest_revenue_movies"], x="budget", y="revenue"
    )
    plt.title("Revenue vs. Budget")
    plt.xlabel("Budget (in millions)")
    plt.ylabel("Revenue (in millions)")
    plt.show()

    # 2. ROI Distribution by Genre
    pandas_df = movie_data_df.select("roi", "genres").toPandas()  # Assuming you have calculated ROI
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=pandas_df, x="genres", y="roi")
    plt.title("ROI Distribution by Genre")
    plt.xlabel("Genre")
    plt.ylabel("ROI")
    plt.xticks(rotation=45, ha="right")
    plt.show()

    # 3. Popularity vs. Rating
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=analysis_results["most_popular_movies"], x="popularity", y="vote_average"
    )
    plt.title("Popularity vs. Rating")
    plt.xlabel("Popularity")
    plt.ylabel("Rating")
    plt.show()
    # 4.Mean Revenue of Franchise vs Standalone
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=analysis_results["franchise_performance_df"], x="belongs_to_collection_name", y="mean_revenue"
    )
    plt.title("Average Revenue: Franchise vs Standalone")
    plt.xlabel("Franchise")
    plt.ylabel("Average Revenue (in millions)")
    plt.xticks(rotation=45, ha="right")
    plt.show()
