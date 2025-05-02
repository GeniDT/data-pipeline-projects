## User Guide: Ecommerce Streaming Pipeline

This guide provides step-by-step instructions to set up and run the Ecommerce Streaming Pipeline, a real-time data processing system that ingests, processes, and stores ecommerce event data using Apache Spark Streaming and PostgreSQL. The project is containerized with Docker for portability and isolation.

## Prerequisites

Before proceeding, ensure the following are installed on your system:

Docker: Version 20.10 or higher.

Docker Compose: Version 1.29 or higher.

Python: Version 3.8 or higher with a virtual environment.

Git: For cloning the project repository.

## Step-by-Step Instructions

1. Clone or Download the Project
Clone the repository or download the project files:

git clone https://github.com/Eugenia-DE/data-portfolio
cd spark_ecommerce_streaming

2. Set Up the Python Virtual Environment
Create and activate a virtual environment:
python -m venv venv
.\venv\Scripts\activate
Install required Python dependencies (e.g., pandas for data_generator.py).

3. Configure PostgreSQL Credentials
The project uses PostgreSQL to store event data.
Open docker-compose.yml in a text editor.
Update the environment section under both postgres and spark services with your preferred credentials.

4. Start Docker Containers
Launch the Spark and PostgreSQL containers:
docker-compose up -d

Verify the containers are running:
docker ps
Expect to see spark_ecommerce_streaming-spark-1 and spark_ecommerce_streaming-postgres-1 with status Up.

6. Initialize the Database
Create the events table in your PostgreSQL database:
docker exec -it spark_ecommerce_streaming-postgres-1 psql -U <your_username> -d <your_database_name>
At the prompt, run:
CREATE TABLE events (
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    PRIMARY KEY (timestamp, user_id, product_id, event_type)
);
\d events
\q

6. Start the Data Generator
Generate synthetic ecommerce event data:
python scripts/data_generator.py
Expected output:
Starting continuous data generation (press Ctrl+C to stop)...
Generated 10 events in data_stream\events_20250502_XXXXXX_X.csv
Keep this running in one terminal window.

7. Run the Spark Streaming Job
Submit the Spark job to process the data and write it to PostgreSQL:
docker exec -it spark_ecommerce_streaming-spark-1 bash
Inside the container, run:
/opt/bitnami/spark/bin/spark-submit \
  --master spark://spark:7077 \
  --jars /opt/bitnami/spark/jars/postgresql-42.7.4.jar \
  /opt/bitnami/spark/scripts/spark_streaming_to_postgres.py
Monitor the output for StreamingQuery Started and file processing messages.
Keep this running in another terminal window.

8. Verify Data in PostgreSQL
Check the number of events in the events table:
docker exec -it spark_ecommerce_streaming-postgres-1 psql -U <your_username> -d <your_database_name> -c "SELECT COUNT(*) FROM events;"
Expected output: A non-zero count (e.g., 10, 20, etc.) after a few seconds.

View sample data:
docker exec -it spark_ecommerce_streaming-postgres-1 psql -U <your_username> -d <your_database_name> -c "SELECT * FROM events LIMIT 5;"

9. Stop the Pipeline
Stop the Spark job by pressing Ctrl+C, then:
exit

10. Stop the data generator by pressing Ctrl+C in its terminal window.
Stop and remove the containers:
docker-compose down