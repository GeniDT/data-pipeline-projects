import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Add scripts directory to Python path
sys.path.append('/opt/airflow/scripts')
from flight_price_pipeline import ingest_data, validate_data, transform_data, load_data

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    'flight_price_analysis',
    default_args=default_args,
    description='A pipeline to ingest, validate, transform, and load Bangladesh flight price data',
    schedule_interval=None, # Set to None for manual triggering since a static dataset is used
    start_date=datetime(year=2025, month=5, day=19),
    catchup=False,
) as dag:
    ingest_task = PythonOperator(task_id='ingest_data', python_callable=ingest_data)
    validate_task = PythonOperator(task_id='validate_data', python_callable=validate_data)
    transform_task = PythonOperator(task_id='transform_data', python_callable=transform_data)
    load_task = PythonOperator(task_id='load_data', python_callable=load_data)
    ingest_task >> validate_task >> transform_task >> load_task