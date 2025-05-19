## Flight Price Analysis Pipeline Report

## Overview
This report documents the Flight Price Analysis pipeline, an Airflow-based data engineering project designed to process flight price data from Bangladesh. The pipeline ingests data from a CSV file, validates it, transforms it to compute key performance indicators (KPIs), and loads the results into an analytics database for reporting. 
The pipeline was executed successfully on May 19, 2025, with a total duration of 00:00:31, as shown in the Airflow UI.

Pipeline Architecture and Execution Flow
Architecture
The pipeline leverages a containerized setup using Docker, orchestrated by docker-compose.yml. Key components include:

Data Source: A static CSV file from Kaggle (Flight_Price_Dataset_of_Bangladesh.csv) stored in /opt/airflow/data/, containing flight price data with columns such as Airline, Total Fare (BDT), Duration (hrs), and Departure Date & Time.
Staging Database: MySQL (flight-price-pipeline-mysql-1), used for staging raw data (flight_data_staging) and transformed data (flight_data_transformed).
Analytics Database: PostgreSQL (flight-price-pipeline-analytics-postgres-1), used to store final KPI results (avg_fare_by_airline table).
Airflow: Apache Airflow (apache/airflow:2.8.1) manages the pipeline with services:
airflow-postgres: Stores Airflow metadata.
airflow-init: Initializes the Airflow database and admin user.
airflow-scheduler: Schedules DAG runs.
airflow-webserver: Provides the UI at http://localhost:8080.



## Execution Flow
The pipeline follows a linear ETL process, executed via the flight_price_analysis DAG:

Ingestion:
Reads Flight_Price_Dataset_of_Bangladesh.csv into a pandas DataFrame.
Validates the presence of required columns (e.g., Airline, Total Fare (BDT)).
Writes the data to the MySQL flight_data_staging table.


Validation:
Reads data from flight_data_staging.
Checks for missing Total Fare (BDT), invalid Duration (hrs) (outside 0-24 range), and invalid Departure Date & Time formats.
Raises an error if validation fails.


Transformation:
Reads data from flight_data_staging.
Computes the average fare per airline using groupby on Airline and mean on Total Fare (BDT).
Saves the result to the MySQL flight_data_transformed table.


Loading:
Reads transformed data from flight_data_transformed.
Loads it into the PostgreSQL avg_fare_by_airline table for analytics.



The flow is managed by Airflow, ensuring each task completes successfully before the next begins (ingest_task >> validate_task >> transform_task >> load_task).
Description of Airflow DAG and Tasks
DAG: flight_price_analysis

File: dags/flight_price_analysis.py
Description: Orchestrates the ETL pipeline for flight price data.
Schedule Interval: Set to None for manual triggering, as this is an assignment and does not require recurring runs.
Start Date: May 19, 2025.
Catchup: Disabled to prevent backfilling.

Tasks

ingest_data:
Python Callable: ingest_data from scripts/flight_price_pipeline.py.
Purpose: Reads the CSV file, validates required columns, and loads data into the MySQL flight_data_staging table.
Output: Populates flight_data_staging with raw data.


validate_data:
Python Callable: validate_data.
Purpose: Ensures data quality by checking for missing fares, invalid durations, and date formats.
Output: Passes if validation succeeds; raises an error otherwise.


transform_data:
Python Callable: transform_data.
Purpose: Computes the average fare per airline and saves it to the MySQL flight_data_transformed table.
Output: Populates flight_data_transformed with transformed data.


load_data:
Python Callable: load_data.
Purpose: Transfers transformed data from MySQL to the PostgreSQL avg_fare_by_airline table.
Output: Populates avg_fare_by_airline for analytics.



## KPI Definitions and Computation Logic
KPI: Average Fare by Airline

Definition: The average total fare (in Bangladeshi Taka, BDT) for each airline, calculated across all flights in the dataset.
Purpose: To provide insights into pricing trends across airlines, useful for cost comparison and decision-making.
Computation Logic:
Read raw data from the flight_data_staging table.
Group the data by Airline and compute the mean of Total Fare (BDT) using pandas:avg_fare_by_airline = df.groupby("Airline")["Total Fare (BDT)"].mean().reset_index()


Rename columns to Airline and Average_Fare_BDT for clarity.
Save the result to the flight_data_transformed table in MySQL, then load it into the avg_fare_by_airline table in PostgreSQL.



## KPI Output
Below is an example output for a KPI result. This was populated by running:
docker exec -it flight-price-pipeline-analytics-postgres-1 psql -U analytics_user -d flight_analytics -c "SELECT * FROM avg_fare_by_airline LIMIT 5;"

Example Output:
          Airline          | Average_Fare_BDT  
---------------------------+-------------------
 Air Arabia                |  69924.0069653591
 Air Astra                 | 68497.40780385124
 Air India                 | 72474.17841927757
 AirAsia                   | 74534.39065085599
 Biman Bangladesh Airlines | 70192.96928740495

Average Price during peak and non-peak sesons
This was computed using:
$ docker exec -it flight-price-pipeline-analytics-postgres-1 psql -U analytics_user -d flight_analytics -c "SELECT * FROM seasonal_fare_variation;"
 Season_Type | Average_Fare_BDT  
-------------+-------------------
 Peak        | 91560.02323587236
 Non-Peak    |  70810.8113784666

Booking Count by Airline was computed using:
$ docker exec -it flight-price-pipeline-analytics-postgres-1 psql -U analytics_user -d flight_analytics -c "SELECT * FROM booking_count_by_airline LIMIT 5;"
          Airline          | Booking_Count 
---------------------------+---------------
 Air Arabia                |          2217
 Air Astra                 |          2304
 Air India                 |          2280
 AirAsia                   |          2312
 Biman Bangladesh Airlines |          2344

Most Popular Routes:
$ docker exec -it flight-price-pipeline-analytics-postgres-1 psql -U analytics_user -d flight_analytics -c "SELECT * FROM popular_routes;"
 Source | Destination | Booking_Count 
--------+-------------+---------------
 RJH    | SIN         |           417
 DAC    | DXB         |           413
 BZL    | YYZ         |           410
 CXB    | DEL         |           408
 CGP    | BKK         |           408


Challenges Encountered and Resolutions
1. airflow-init Container Stuck in "Waiting" State

Issue: The flight-price-pipeline-airflow-init-1 container was stuck in a "Waiting" state for over 513 seconds due to a syntax error in the docker-compose.yml file’s airflow-init command:/bin/bash: -c: line 13: syntax error near unexpected token `)'
/bin/bash: -c: line 13: `         echo 'Init completed successfully')'


Resolution:
Identified an extra parenthesis in the command section and removed it.
Updated docker-compose.yml and restarted services with docker-compose down -v and docker-compose up -d.
Verified the fix by checking logs and ensuring airflow-init completed successfully.


2. Dependency Installation Permission Issue

Issue: Attempting to install dependencies via pip install -r /opt/airflow/requirements.txt resulted in a permission error:bash: /root/bin/pip: Permission denied


Resolution:
The apache/airflow:2.8.1 image runs as the airflow user, not root. Modified the airflow-init service in docker-compose.yml to install dependencies using pip install --user.
Confirmed that the pipeline ran successfully even without this step due to pre-installed dependencies in the image, but recommended installing for future stability.


3. Daily Schedule Interval Not Suitable

Issue: Contemplating if DAG should be set to run daily (schedule_interval='@daily'), which I believe would be unnecessary for an assignment with a static dataset.
Resolution:
Chose schedule_interval to None in flight_price_analysis.py to allow manual triggering.



## Conclusion
The Flight Price Analysis pipeline successfully processes flight price data from a CSV file, validates it, computes the average fare by airline, and loads the results into a PostgreSQL analytics database. The use of Airflow ensures a robust and manageable ETL process, while Docker provides a consistent environment. Challenges were addressed systematically, ensuring the pipeline’s reliability. The KPI results provide valuable insights into airline pricing trends.
For further details, refer to the project’s README.md for setup instructions, or review the logs in /opt/airflow/logs/pipeline.log.
