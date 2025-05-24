## Test Cases: Real-Time Data Ingestion Pipeline
This document outlines manual test cases to verify the functionality of the real-time e-commerce data pipeline. Each test case includes a description, steps, expected outcome, actual outcome and pass/fail criteria. The pipeline continuously generates CSV files, processes them with Spark Structured Streaming, and stores events in a PostgreSQL database.

## Test Case 1: Docker Containers Start Successfully
Description: Verify that all Docker containers (PostgreSQL, Spark, data generator) start without errors.
Steps:

Navigate to the project root: cd ecommerce-pipeline.
Ensure config/.env and config/docker-compose.yml are present.
Run: docker-compose up -d.
Check container status: docker ps.

Expected Outcome:

Three containers running: postgres, spark, data-generator.
No containers in "Exited" state.

Actual Outcome: 

CONTAINER ID   IMAGE                                  
    COMMAND                  CREATED          STATUS                    PORTS                    NAMES      
7b63ed380336   spark_ecommerce_streaming-spark            "/app/entry.sh"          54 minutes ago   Up 54 minutes                                      spark      
066586f4fa87   spark_ecommerce_streaming-data-generator   "python /app/data_ge…"   54 minutes ago   Up 54 minutes                                      data-generator
284cdb70d59e   postgres:latest                        
    "docker-entrypoint.s…"   54 minutes ago   Up 54 minutes (healthy)   0.0.0.0:5432->5432/tcp   postgres 

Pass: All three containers are running (docker ps shows "Up").
Fail: Any container is missing or exited.

## Test Case 2: PostgreSQL Database and Table Created
Description: Verify that the ecommerce database and user_events table are created with the correct schema.
Steps:

Run: docker exec -it postgres psql -U admin -d ecommerce -c "\d user_events".
Inspect the table schema.

Expected Outcome:

Table user_events exists with columns:
event_id (serial, primary key)
user_id (varchar(50), not null)
action (varchar(20), not null)
product_id (integer, not null)
timestamp (timestamp, not null)
created_at (timestamp, default current_timestamp)



Actual Outcome: 
                Table "public.user_events"
   Column   |            Type             | Collation | Nullable | Default 
------------+-----------------------------+-----------+----------+---------
 event_id   | integer                     |           | not null | 
 user_id    | character varying(50)       |           | not null | 
 action     | character varying(50)       |           | not null | 
 product_id | integer                     |           | not null | 
 timestamp  | timestamp without time zone |           | not null |
 created_at | timestamp without time zone |           |          |
Indexes:
    "user_events_pkey" PRIMARY KEY, btree (event_id)

Pass/Fail Criteria:

Pass: Table exists with correct columns and constraints.
Fail: Table missing, incorrect schema, or missing constraints.

## Test Case 3: Data Generator Produces Continuous CSV Files
Description: Verify that data_generator.py continuously generates CSV files with the correct schema.
Steps:

Start containers: docker-compose up -d data-generator.
Wait for ~200 seconds (approximating ~100 files at 2 seconds per file).
Stop the data generator: docker stop data-generator.
Check logs: cat logs/data_generator.log.
If data/csv/ is mounted locally, count files: ls -l data/csv/ | wc -l.
Inspect a sample CSV (e.g., data/csv/events_20250521_223000_001.csv).

Expected Outcome:

logs/data_generator.log shows ~100 files generated (e.g., "Generated file events_20250521_223000_001.csv").
~100 files in data/csv/ (if mounted).
Sample CSV has columns: user_id (string), action (view/purchase), product_id (integer), timestamp (ISO 8601 string).
No null values in any column.

Actual Outcome: 
2025-05-24 00:10:56,434 INFO Generated event_id: 33621
2025-05-24 00:10:56,444 INFO Generated 100 records in /csv-data/events_1748045456.csv with event_ids 33522 to 33621
2025-05-24 00:11:01,450 INFO Starting data generation for 100 records
2025-05-24 00:11:01,488 INFO Generated event_id: 33622
2025-05-24 00:11:01,508 INFO Generated event_id: 33623
2025-05-24 00:11:01,526 INFO Generated event_id: 33624

Pass/Fail Criteria:

Pass: ~100 files after 200 seconds, correct schema, no nulls.
Fail: Significantly fewer files, incorrect schema, or null values.

## Test Case 4: Spark Detects and Processes CSV Files
Description: Verify that the Spark job detects and processes CSV files with maxFilesPerTrigger=10.
Steps:

Run the data generator for ~200 seconds and stop it (see Test Case 3).
Run the Spark job: docker exec spark spark-submit /app/spark_streaming_to_postgres.py.
Check logs: cat logs/spark_streaming.log.
After completion, verify no files remain in data/csv/ (Spark moves processed files).

Expected Outcome:

logs/spark_streaming.log shows 10 batches (100 files ÷ 10 per trigger).
Log entries like "Batch X written to PostgreSQL: ~500 rows".

Actual Outcome: 
2025-05-24 00:10:44,458 INFO Received command c on object id p1
2025-05-24 00:10:44,596 INFO Batch 59 written to PostgreSQL
2025-05-24 00:10:45,752 INFO Received command c on object id p0
2025-05-24 00:10:45,756 INFO Sample rows for batch 60:
2025-05-24 00:10:50,886 INFO Received command c on object id p0
2025-05-24 00:10:50,889 INFO Sample rows for batch 61:
2025-05-24 00:10:51,553 INFO Received command c on object id p1
2025-05-24 00:10:51,691 INFO Batch 60 written to PostgreSQL

Pass/Fail Criteria:

Pass: ~100 files processed, ~10 batches logged, no files remain.
Fail: Files not processed, incorrect batch count, or errors in logs.

## Test Case 5: Data Transformations Are Correct
Description: Verify that Spark applies the specified transformations (null removal, action validation, timestamp casting).
Steps:

Run the Spark job (see Test Case 4).
Query the database: docker exec -it postgres psql -U admin -d ecommerce -c "SELECT * FROM user_events LIMIT 10".
Check for nulls: docker exec -it postgres psql -U admin -d ecommerce -c "SELECT COUNT(*) FROM user_events WHERE user_id IS NULL OR action IS NULL OR product_id IS NULL OR timestamp IS NULL".
Check valid actions: docker exec -it postgres psql -U admin -d ecommerce -c "SELECT DISTINCT action FROM user_events".

Expected Outcome:

Sample rows show user_id (string), action (view/purchase), product_id (integer), timestamp (valid timestamp).
Null count is 0.
action values are only "view" or "purchase".

Actual Outcome: 
 count 
-------
     0
(1 row)

   action    
-------------
 add_to_cart
 view
 purchase
 click
(4 rows)


Pass/Fail Criteria:

Pass: No nulls, only valid actions, timestamp as valid timestamps.
Fail: Null values, invalid actions, or incorrect timestamp format.

## Test Case 6: Data Written to PostgreSQL
Description: Verify that events are written to the user_events table without errors.
Steps:

Run the Spark job after ~200 seconds of data generation (see Test Case 4).
Check row count: docker exec -it postgres psql -U admin -d ecommerce -c "SELECT COUNT(*) FROM user_events".
Check event_id and created_at: docker exec -it postgres psql -U admin -d ecommerce -c "SELECT event_id, created_at FROM user_events LIMIT 5".
Check logs for errors: cat logs/spark_streaming.log.

Expected Outcome:

Row count is 5,000 (100 files × 50 events).
event_id is unique and auto-incremented.
created_at is a valid timestamp (defaulted by PostgreSQL).
No write errors in logs/spark_streaming.log.

Actual Outcome: 
 count 
-------
 81800
(1 row)

event_id |         created_at
----------+----------------------------
        1 | 2025-05-23 10:00:51.818596
        2 | 2025-05-23 10:00:51.849415
        3 | 2025-05-23 10:00:51.871253
        4 | 2025-05-23 10:00:51.892546
        6 | 2025-05-23 10:00:51.940678
(5 rows)

Pass/Fail Criteria:

Pass: ~5,000 rows, unique event_id, valid created_at, no errors.
Fail: Incorrect row count, duplicate event_id, or write errors.

## Test Case 7: Logging to Files
Description: Verify that all logging occurs in files, not the console.
Steps:

Run the data generator and Spark job (see Test Cases 3 and 4).
Check log files: cat logs/data_generator.log and cat logs/spark_streaming.log.
During Spark job execution, monitor console output: docker logs spark.

Expected Outcome:

logs/data_generator.log contains entries for files (e.g., "Generated file events_20250521_223000_001.csv").
logs/spark_streaming.log contains entries for initialization, batches, and writes.
docker logs spark shows minimal output (only WARN/ERROR from Spark).

Actual Outcome: 
2025-05-24 01:01:11,372 INFO Generated event_id: 74206
2025-05-24 01:01:11,395 INFO Generated event_id: 74207
2025-05-24 01:01:11,429 INFO Generated event_id: 74208
2025-05-24 01:01:11,457 INFO Generated event_id: 74209
2025-05-24 01:01:11,479 INFO Generated event_id: 74210
2025-05-24 01:01:11,499 INFO Generated event_id: 74211

2025-05-24 00:10:50,886 INFO Received command c on object id p0
2025-05-24 00:10:50,889 INFO Sample rows for batch 61:
2025-05-24 00:10:51,553 INFO Received command c on object id p1
2025-05-24 00:10:51,691 INFO Batch 60 written to PostgreSQL
2025-05-24 00:10:58,823 INFO Received command c on object id p0
2025-05-24 00:10:58,826 INFO Sample rows for batch 62:


Pass/Fail Criteria:

Pass: Logs in files, minimal console output.
Fail: Missing log entries or excessive console output.

## Test Case 8: Error Handling
Description: Verify that the pipeline handles errors (e.g., invalid CSV, database connection failure) and logs them.
Steps:

Create an invalid CSV in data/csv/ (e.g., missing user_id column) and run the Spark job.
Temporarily stop PostgreSQL: docker stop postgres and run the Spark job.
Check logs: cat logs/spark_streaming.log.
Restart PostgreSQL: docker start postgres and rerun the Spark job to verify recovery.

Expected Outcome:

For invalid CSV: logs/spark_streaming.log shows read error, job continues or stops gracefully.
For database failure: logs/spark_streaming.log shows connection error, job retries or stops.
After recovery: Job processes remaining files and writes to PostgreSQL.

Pass/Fail Criteria:

Pass: Errors logged, job handles failures gracefully, recovers after restart.
Fail: Unlogged errors, job crashes, or no recovery.
