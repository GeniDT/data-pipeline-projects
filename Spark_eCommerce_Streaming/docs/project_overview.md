## Project Overview: Real-Time Data Ingestion Pipeline

## Introduction
This project implements a real-time data pipeline simulating an e-commerce platform tracking user activity (product views and purchases). It uses Apache Spark Structured Streaming to process data in real-time, PostgreSQL to store processed events, and Docker to manage the environment. The pipeline continuously generates CSV files, processes them with data cleaning and type conversion, and stores events in a database, meeting objectives of real-time processing, data transformation, and performance evaluation.

## Components
The pipeline consists of four main components, orchestrated via Docker:

Data Generator (scripts/data_generator.py):
Continuously generates CSV files, each with 50 e-commerce events, until stopped.
Events include user_id (string), action (view/purchase), product_id (integer), and timestamp (ISO 8601 string).
Writes files to the csv-data volume (/csv-data) with a 2-second delay between files.
Logs activities to logs/data_generator.log.


Spark Structured Streaming (scripts/spark_streaming_to_postgres.py):
Monitors /csv-data for new CSV files using Spark Structured Streaming.
Processes up to 10 files per trigger (maxFilesPerTrigger=10) in batches.
Applies transformations: removes null values, validates action (view/purchase), casts timestamp to a timestamp type.
Writes processed events to the PostgreSQL user_events table via JDBC.
Logs activities to logs/spark_streaming.log.


PostgreSQL Database (scripts/postgres_setup.sql):
Initializes the ecommerce database and user_events table.
Table schema: event_id (serial, primary key), user_id (varchar), action (varchar), product_id (integer), timestamp (timestamp), created_at (timestamp, default).
Stores events as they are processed, with event_id and created_at auto-generated.


Docker Environment (config/docker-compose.yml, config/.env):
Runs three containers: postgres (PostgreSQL), spark (Bitnami Spark 3.5.0), data-generator (Python 3.9).
Uses a shared csv-data volume for CSVs, spark-checkpoints for fault tolerance, and logs/ for logging.
Connects containers via the ecommerce-pipeline-net network.
Manages credentials in config/.env (e.g., POSTGRES_USER, POSTGRES_PASSWORD).



## Data Flow

CSV Generation: The data generator continuously creates CSV files in /csv-data, each with 50 events (user_id, action, product_id, timestamp).
Spark Processing: Spark monitors /csv-data, reads files in batches (10 files per trigger), removes nulls, validates actions, casts timestamps, and prepares data for storage.
Database Storage: Spark writes processed events to the ecommerce.user_events table via JDBC, accumulating rows over time.
Logging: All activities (file generation, processing, errors) are logged to logs/data_generator.log and logs/spark_streaming.log.

## Key Features

Real-Time Processing: Spark Structured Streaming processes files as they appear, simulating a continuous e-commerce stream.
Data Transformations: Cleans null values and validates actions (view/purchase), with timestamp casting to match the database schema.
Error Handling: Logs errors (e.g., invalid CSVs, database connection issues) to files, ensuring graceful failure handling.
Performance: Processes ~5,000 events in ~100–200 seconds (for ~100 files), with throughput ~25–50 events/second.
Docker: Simplifies setup with containerized Spark, PostgreSQL, and data generator, using a shared volume and network.


## Deliverables

Scripts: data_generator.py, spark_streaming_to_postgres.py, postgres_setup.sql.
Configuration: docker-compose.yml, .env, postgres_connection_details.txt.
Documentation: user_guide.md (setup instructions), test_cases.md (test plan), performance_metrics.md (performance data), system_architecture.png (diagram).

## Conclusion
The pipeline demonstrates real-time data ingestion, processing, and storage using Spark Structured Streaming and PostgreSQL in a Dockerized environment. It handles continuous CSV generation with robust error handling, file-based logging, and specified transformations, meeting all learning objectives for real-time data pipelines.