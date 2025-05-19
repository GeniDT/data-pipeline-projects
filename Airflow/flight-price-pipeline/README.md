## Flight Price Analysis Pipeline
## Overview
This project implements an ETL (Extract, Transform, Load) pipeline using Apache Airflow to process flight price data from Bangladesh. The pipeline ingests data from a CSV file, validates it, transforms it to compute key performance indicators (KPIs), and loads the results into a PostgreSQL analytics database. 

## Features

Ingests flight price data from Flight_Price_Dataset_of_Bangladesh.csv.
Validates data for quality (e.g., missing fares, invalid durations).
Computes KPIs:
Average Fare by Airline
Seasonal Fare Variation (peak vs. non-peak seasons)
Booking Count by Airline
Most Popular Routes (top source-destination pairs)


Uses Docker for containerized deployment with MySQL (staging) and PostgreSQL (analytics).

## Prerequisites

Docker and Docker Compose
Python 3.8+
Airflow dependencies (listed in requirements.txt)
Access to the dataset: Flight_Price_Dataset_of_Bangladesh.csv (place in data/ directory)

Directory Structure
flight-price-pipeline/
├── dags/                    # Airflow DAG definitions
│   └── flight_price_analysis.py
├── scripts/                 # Pipeline scripts
│   └── flight_price_pipeline.py
├── data/                    # Data files (not committed to Git)
│   └── Flight_Price_Dataset_of_Bangladesh.csv
├── docs/                    # Detailed documentation
│   └── flight_price_analysis_report.md
├── logs/                    # Airflow logs (not committed to Git)
├── docker-compose.yml       # Docker Compose configuration
├── init-postgres.sql        # PostgreSQL initialization script
├── init_mysql.sql           # MySQL initialization script
├── requirements.txt         # Python dependencies
└── README.md                # Project overview

Setup Instructions

Clone the Repository:git clone <repository-url>
cd flight-price-pipeline


Generate a Fernet Key (if not already set in docker-compose.yml):python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Replace your_fernet_key_here== in docker-compose.yml with the generated key.
Start Services:docker-compose up -d


Access Airflow UI:
URL: http://localhost:8080
Login: admin / admin


Trigger the DAG:
In the Airflow UI, locate the flight_price_analysis DAG.
Trigger it manually (schedule interval is set to None).



## Documentation
For a detailed report on the pipeline architecture, execution flow, DAG/task descriptions, KPI definitions, and challenges, refer to docs/flight_price_analysis_report.md.
