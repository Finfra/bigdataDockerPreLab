# dags/fms_data_pipeline.py
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'fms-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'fms-data-pipeline',
    default_args=default_args,
    schedule_interval='0 * * * *',  # 매시간 실행
    start_date=datetime(2024, 1, 1)
)

# 작업 정의
collect_data = BashOperator(
    task_id='collect_fms_data',
    bash_command='python /opt/fms/collector/main.py',
    dag=dag
)

process_data = BashOperator(
    task_id='process_streaming_data',
    bash_command='spark-submit /opt/spark-apps/fms-processor.py',
    dag=dag
)

quality_check = BashOperator(
    task_id='data_quality_check',
    bash_command='python /opt/fms/quality/validator.py',
    dag=dag
)

# 작업 의존성
collect_data >> process_data >> quality_check