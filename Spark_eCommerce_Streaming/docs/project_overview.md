## Real-Time Data Ingestion Using Spark Structured Streaming & PostgreSQL 

## Introduction
This project focuses on building a real-time data pipeline for simulated e-commerce events. It involves generating fake user activity data as CSV files, leverages Apache Spark Streaming for processing, PostgreSQL for persistent storage, and Docker for containerized deployment. 

## System Components
1. data_generator.py
Purpose: Simulates and outputs a continuous stream of e-commerce events.
Functionality:
Produces CSV files every 2 seconds in the data_stream/ directory.
Each file contains 10 events with columns: timestamp (ISO format, e.g., 2025-05-01T12:03:13.904182), user_id (UUID), product_id (e.g., product_20), and event_type (view or purchase).
Includes a header row (timestamp,user_id,product_id,event_type).

2. spark_streaming_to_postgres.py
Purpose: Continuously monitors, processes, and transforms the incoming stream of e-commerce events.
Functionality:
Runs on Apache Spark in a Docker container (spark_ecommerce_streaming-spark-1).
Reads CSV files from /opt/bitnami/spark/data_stream using a predefined schema.
Skips the CSV header row using .option("header", "true").
Converts the timestamp column to TimestampType.
Writes processed data to the PostgreSQL events table in append mode.
Uses a checkpoint directory (/opt/bitnami/spark/checkpoint) to track processed files.

3. postgres_setup.sql 
Purpose: 
Persistently stores the processed e-commerce event data in a structured format.
Functionality:
Runs in a Docker container (spark_ecommerce_streaming-postgres-1).
Role: Receives streaming data from Spark and supports queries (e.g., SELECT COUNT(*) FROM events;).

4. docker-compose.yml: To define and manage the multi-container Docker environment for the PostgreSQL database and potentially the Spark application.
Configuration:
Spark Service:
Image: bitnami/spark:3.5.
Ports: 7077 (Spark master), 8080 (Spark UI).
Volume mounts: data_stream/ and checkpoint/ for data and state persistence.
PostgreSQL Service:
Image: postgres:15.
Port: 5432.
Environment variables for database setup.
Volumes: Maps host directories (./data_stream, ./checkpoint) to container paths.


## Data Flow
Event Generation:
The data generator (data_generator.py) runs on the host, producing CSV files in data_stream/ every 2 seconds.
Each file contains 10 events with a header row.

Streaming Ingestion:
The Spark streaming job (spark_streaming_to_postgres.py) monitors /opt/bitnami/spark/data_stream (mapped to host data_stream/).
Reads new CSV files using a schema, skipping headers.
Converts timestamp to TimestampType.

Data Processing:
Processes data in micro-batches, writing each batch to PostgreSQL.

Uses the PostgreSQL JDBC driver to connect to postgres:5432/ecommerce.

Data Storage:
Appends events to the events table in PostgreSQL.
Maintains checkpoint data in /opt/bitnami/spark/checkpoint to ensure fault tolerance.

Monitoring and Verification:
Users can query the events table (e.g., SELECT COUNT(*) FROM events;) to verify data ingestion.

The Spark UI (http://localhost:8080) provides streaming query metrics.