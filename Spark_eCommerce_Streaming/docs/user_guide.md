## User Guide: Real-Time Data Ingestion Pipeline
This guide provides instructions to set up and run the real-time e-commerce data pipeline using Docker, Apache Spark Structured Streaming, and PostgreSQL.
Prerequisites

Docker: Install Docker Desktop (Windows) and Docker Compose (version 3.8+).
Project Files:Spark_eCommerce_Streaming/
├── scripts/
│   ├── data_generator.py
│   ├── spark_streaming_to_postgres.py
│   ├── postgres_setup.sql
│   ├── entry.sh
├── docs/
│   ├── user_guide.md (this file)
│   ├── project_overview.md
│   ├── test_cases.md
│   ├── performance_metrics.md
├── data/
│   ├── csv/
│   ├── checkpoints/
│   ├── postgres/
├── logs/
├── docker-compose.yml
├── Dockerfile.spark
├── Dockerfile.data-generator
├── .env



## Setup Instructions

Create .env File with Postgres credentials

Add to .gitignore:echo .env >> .gitignore


## Set Up Directories

Create:mkdir scripts,docs,data\csv,data\checkpoints,data\postgres,logs


Create Entry Script

Start Containers

Navigate to project root:cd $env:USERPROFILE\OneDrive\Desktop\Data_Engineer_Amalitech\LABS\Spark_eCommerce_Streaming


Build and start:docker-compose -f docker-compose.yml up -d --build


Verify:docker ps




## Verify PostgreSQL

Check table:docker exec -it postgres psql -U admin -d ecommerce -c "\d user_events"


Run Data Generator

Check logs:cat logs\data_generator.log


Verify CSVs:dir data\csv\


Stop:docker stop data-generator




## Verify Spark Job

Check logs:docker logs spark
cat logs\spark_streaming.log




## Verify Database

Check rows:docker exec -it postgres psql -U admin -d ecommerce -c "SELECT COUNT(*) FROM user_events"


View data:docker exec -it postgres psql -U admin -d ecommerce -c "SELECT * FROM user_events LIMIT 10"





## Troubleshooting

Verify data_generator.py produces valid data. Rebuild:docker-compose -f docker-compose.yml down -v
docker-compose -f docker-compose.yml build --no-cache spark data-generator
docker-compose -f docker-compose.yml up -d --build

Check:docker logs spark
cat logs\spark_streaming.log


Spark Container Exits with Permission Denied:
Symptom: cp: cannot create regular file '/app/spark_streaming_to_postgres.py': Permission denied.
Fix: Ensure Dockerfile.spark sets permissions:RUN chmod +x /app/entry.sh && \
    chown 1001:1001 /app /scripts /scripts/spark_streaming_to_postgres.py /app/entry.sh && \
    chmod 755 /app /scripts && \
    chmod 644 /scripts/spark_streaming_to_postgres.py




No Spark Logs:
Symptom: logs\spark_streaming.log missing.
Fix: Check:docker logs spark




NumPy/Pandas Incompatibility:
Symptom: ValueError: numpy.dtype size changed.
Fix: Ensure Dockerfile.data-generator pins numpy==1.24.3.






## Verification

CSV Files: Check logs\data_generator.log and data/csv/*.csv.
Transformations: Check logs/spark_streaming.log for sample rows.
Database Writes: Confirm row count.
Performance: Time Spark job.

## Cleanup

Stop:docker-compose -f docker-compose.yml down


Remove volumes:docker volume rm config_postgres-data config_csv-data config_spark-checkpoints