"""
Retail ETL Pipeline DAG
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="retail_pipeline",
    default_args=default_args,
    description="Daily ETL pipeline: extract - transform - load retail movements",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["retail", "etl", "pipeline"],
) as dag:

    extract = BashOperator(
        task_id="extract_raw_movements",
        bash_command="cd /opt/airflow && python pipeline/extract/extract_raw_movements.py",
    )

    transform = BashOperator(
        task_id="transform_raw_movements",
        bash_command="cd /opt/airflow && python pipeline/transform/transform_raw_movements.py",
    )

    load = BashOperator(
        task_id="load_movements",
        bash_command="cd /opt/airflow && python pipeline/load/load_movements.py",
    )

    extract >> transform >> load
