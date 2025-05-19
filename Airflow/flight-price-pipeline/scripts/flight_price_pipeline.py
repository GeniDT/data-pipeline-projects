import os
import pandas as pd
from sqlalchemy import create_engine
import logging
from dotenv import load_dotenv

# Load environment variables from a .env file to configure database connections and other settings
load_dotenv()

# Configure logging to record information and errors to a file in the Airflow logs directory
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/opt/airflow/logs/pipeline.log"),  # Log to a file in the Airflow logs directory
    ]
)
logger = logging.getLogger("pipeline")  # Create a logger instance for this pipeline

def ingest_data(csv_path="/opt/airflow/data/Flight_Price_Dataset_of_Bangladesh.csv", table_name="flight_data_staging"):
    """
    Ingest data from a CSV file into a MySQL staging table.
    Args:
        csv_path (str): Path to the CSV file containing flight price data.
        table_name (str): Name of the MySQL table to store the ingested data.
    Raises:
        FileNotFoundError: If the CSV file is not found.
        ValueError: If required columns are missing.
        Exception: For other ingestion errors.
    """
    try:
        logger.info(f"Reading CSV from {csv_path}")  # Log the start of CSV reading
        df = pd.read_csv(csv_path)  # Read the CSV file into a pandas DataFrame
        logger.info(f"Loaded {len(df)} rows from CSV")  # Log the number of rows loaded
        
        required_columns = [
            "Airline", "Source", "Source Name", "Destination", "Destination Name",
            "Departure Date & Time", "Arrival Date & Time", "Duration (hrs)", "Stopovers",
            "Aircraft Type", "Class", "Booking Source", "Base Fare (BDT)",
            "Tax & Surcharge (BDT)", "Total Fare (BDT)", "Seasonality", "Days Before Departure"
        ]  # Define the expected columns in the CSV
        missing_columns = [col for col in required_columns if col not in df.columns]  # Check for missing columns
        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}")  # Log missing columns
            raise ValueError(f"Missing required columns: {missing_columns}")  # Raise error if columns are missing
        
        mysql_user = os.getenv("MYSQL_USER", "flight_user")  # Get MySQL username from environment or default
        mysql_password = os.getenv("MYSQL_PASSWORD", "flight_pass")  # Get MySQL password from environment or default
        mysql_host = os.getenv("MYSQL_HOST", "mysql")  # Get MySQL host from environment or default
        mysql_port = os.getenv("MYSQL_PORT", "3306")  # Get MySQL port from environment or default
        mysql_database = os.getenv("MYSQL_DATABASE", "flight_staging")  # Get MySQL database from environment or default
        
        logger.info(f"Connecting to MySQL - Host: {mysql_host}, Port: {mysql_port}, User: {mysql_user}, Database: {mysql_database}")  # Log connection details
        mysql_conn_string = (
            f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        )  # Construct the MySQL connection string
        engine = create_engine(mysql_conn_string)  # Create a SQLAlchemy engine for MySQL
        
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)  # Write DataFrame to MySQL table, replacing if it exists
        logger.info(f"Successfully loaded {len(df)} rows into {table_name}")  # Log successful ingestion
    except FileNotFoundError as e:
        logger.error(f"CSV file not found: {e}")  # Log file not found error
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")  # Log validation error
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")  # Log any other ingestion errors
        raise

def validate_data(table_name="flight_data_staging"):
    """
    Validate the data in the MySQL staging table.
    Args:
        table_name (str): Name of the MySQL table to validate.
    Raises:
        ValueError: If validation checks fail (e.g., missing fares, invalid durations).
        Exception: For other validation errors.
    """
    try:
        mysql_conn_string = (
            f"mysql+mysqlconnector://{os.getenv('MYSQL_USER', 'flight_user')}:{os.getenv('MYSQL_PASSWORD', 'flight_pass')}"
            f"@{os.getenv('MYSQL_HOST', 'mysql')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DATABASE', 'flight_staging')}"
        )  # Construct the MySQL connection string using environment variables
        engine = create_engine(mysql_conn_string)  # Create a SQLAlchemy engine for MySQL
        logger.info(f"Connected to MySQL for validation")  # Log successful connection
        
        df = pd.read_sql_table(table_name, engine)  # Read the table into a DataFrame
        logger.info(f"Loaded {len(df)} rows for validation")  # Log the number of rows loaded
        
        issues = []  # List to store validation issues
        if df["Total Fare (BDT)"].isnull().any():  # Check for missing total fares
            issues.append("Missing values in Total Fare (BDT)")
        if not df["Duration (hrs)"].between(0, 24).all():  # Check if durations are between 0 and 24 hours
            issues.append("Invalid Duration (hrs) values (outside 0-24 range)")
        if not pd.to_datetime(df["Departure Date & Time"], errors='coerce').notna().all():  # Validate date format
            issues.append("Invalid Departure Date & Time format")
        
        if issues:  # If any issues are found
            logger.error(f"Validation failed: {', '.join(issues)}")  # Log the validation failures
            raise ValueError(f"Validation errors: {', '.join(issues)}")  # Raise an error with details
        logger.info("Validation passed successfully")  # Log successful validation
    except Exception as e:
        logger.error(f"Validation error: {e}")  # Log any other validation errors
        raise

def transform_data(source_table="flight_data_staging", target_table="flight_data_transformed"):
    """
    Transform the data by calculating multiple KPIs:
    - Average Fare by Airline
    - Seasonal Fare Variation (peak vs. non-peak seasons)
    - Booking Count by Airline
    - Most Popular Routes (top source-destination pairs by booking count)
    Args:
        source_table (str): Source MySQL table to transform.
        target_table (str): Target MySQL table to store transformed data (not used directly; see notes).
    Raises:
        Exception: For any transformation errors.
    """
    try:
        mysql_conn_string = (
            f"mysql+mysqlconnector://{os.getenv('MYSQL_USER', 'flight_user')}:{os.getenv('MYSQL_PASSWORD', 'flight_pass')}"
            f"@{os.getenv('MYSQL_HOST', 'mysql')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DATABASE', 'flight_staging')}"
        )  # Construct the MySQL connection string
        engine = create_engine(mysql_conn_string)  # Create a SQLAlchemy engine for MySQL
        logger.info("Connected to MySQL for transformation")  # Log successful connection
        
        df = pd.read_sql_table(source_table, engine)  # Read the source table into a DataFrame
        logger.info(f"Loaded {len(df)} rows for transformation")  # Log the number of rows loaded

        # KPI 1: Average Fare by Airline
        avg_fare_by_airline = df.groupby("Airline")["Total Fare (BDT)"].mean().reset_index()
        avg_fare_by_airline.columns = ["Airline", "Average_Fare_BDT"]
        avg_fare_by_airline.to_sql("avg_fare_by_airline", con=engine, if_exists="replace", index=False)
        logger.info(f"Computed Average Fare by Airline with {len(avg_fare_by_airline)} rows")

        # KPI 2: Seasonal Fare Variation
        # Define peak seasons based on 'Seasonality' or 'Departure Date & Time'
        # Assuming 'Seasonality' contains values like 'Eid' or 'Winter' (adjust based on dataset)
        df['Departure Date & Time'] = pd.to_datetime(df['Departure Date & Time'])
        peak_seasons = df[df['Seasonality'].isin(['Eid', 'Winter'])]  # Define peak seasons
        non_peak_seasons = df[~df['Seasonality'].isin(['Eid', 'Winter'])]
        seasonal_fare_variation = pd.DataFrame({
            'Season_Type': ['Peak', 'Non-Peak'],
            'Average_Fare_BDT': [
                peak_seasons["Total Fare (BDT)"].mean(),
                non_peak_seasons["Total Fare (BDT)"].mean()
            ]
        })
        seasonal_fare_variation.to_sql("seasonal_fare_variation", con=engine, if_exists="replace", index=False)
        logger.info(f"Computed Seasonal Fare Variation with {len(seasonal_fare_variation)} rows")

        # KPI 3: Booking Count by Airline
        booking_count_by_airline = df.groupby("Airline").size().reset_index(name="Booking_Count")
        booking_count_by_airline.to_sql("booking_count_by_airline", con=engine, if_exists="replace", index=False)
        logger.info(f"Computed Booking Count by Airline with {len(booking_count_by_airline)} rows")

        # KPI 4: Most Popular Routes
        # Use 'Source' and 'Destination' for route pairs
        popular_routes = df.groupby(['Source', 'Destination']).size().reset_index(name="Booking_Count")
        popular_routes = popular_routes.sort_values(by="Booking_Count", ascending=False).head(5)  # Top 5 routes
        popular_routes.to_sql("popular_routes", con=engine, if_exists="replace", index=False)
        logger.info(f"Computed Most Popular Routes with {len(popular_routes)} rows")

    except Exception as e:
        logger.error(f"Transformation error: {e}")  # Log any transformation errors
        raise

def load_data(source_table="flight_data_transformed", target_table="avg_fare_by_airline"):
    """
    Load the transformed data from MySQL to a PostgreSQL analytics table.
    Args:
        source_table (str): Source MySQL table to load from (not used directly; see notes).
        target_table (str): Target PostgreSQL table to load into (not used directly; see notes).
    Raises:
        Exception: For any loading errors.
    """
    try:
        mysql_conn_string = (
            f"mysql+mysqlconnector://{os.getenv('MYSQL_USER', 'flight_user')}:{os.getenv('MYSQL_PASSWORD', 'flight_pass')}"
            f"@{os.getenv('MYSQL_HOST', 'mysql')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DATABASE', 'flight_staging')}"
        )  # Construct the MySQL connection string
        pg_conn_string = (
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'analytics_user')}:{os.getenv('POSTGRES_PASSWORD', 'analytics_pass')}"
            f"@{os.getenv('POSTGRES_HOST', 'analytics-postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DATABASE', 'flight_analytics')}"
        )  # Construct the PostgreSQL connection string
        mysql_engine = create_engine(mysql_conn_string)  # Create a SQLAlchemy engine for MySQL
        pg_engine = create_engine(pg_conn_string)  # Create a SQLAlchemy engine for PostgreSQL
        logger.info("Connected to MySQL and PostgreSQL for loading")  # Log successful connections

        # Load all KPI tables from MySQL to PostgreSQL
        for table in ["avg_fare_by_airline", "seasonal_fare_variation", "booking_count_by_airline", "popular_routes"]:
            df = pd.read_sql_table(table, mysql_engine)
            logger.info(f"Loaded {len(df)} rows from {table}")
            df.to_sql(table, pg_engine, if_exists="replace", index=False)
            logger.info(f"Loaded {len(df)} rows into {table} in PostgreSQL")

    except Exception as e:
        logger.error(f"Loading error: {e}")  # Log any loading errors
        raise

if __name__ == "__main__":
    # Execute the full pipeline when the script is run directly
    ingest_data()
    validate_data()
    transform_data()
    load_data()