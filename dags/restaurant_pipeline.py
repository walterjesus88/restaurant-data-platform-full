# from airflow import DAG
# from airflow.operators.bash import BashOperator
# from datetime import datetime

# default_args = {
#     "owner": "data-engineering",
#     "start_date": datetime(2026, 1, 1)
# }

# with DAG(
#     dag_id="restaurant_batch_pipeline",
#     default_args=default_args,
#     schedule="@daily",
#     catchup=False
# ) as dag:

#     load_staging = BashOperator(
#         task_id="load_staging",
#         bash_command="python batch/load_sales.py"
#     )

#     run_incremental = BashOperator(
#         task_id="run_incremental",
#         bash_command="bq query --use_legacy_sql=false < sql/incremental.sql"
#     )

#     load_staging >> run_incremental


from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
from pathlib import Path

DAG_FOLDER = Path(__file__).parent

default_args = {
    "owner": "data-engineering",
    "start_date": datetime(2026, 1, 1),
    "retries": 1
}

with DAG(
    dag_id="restaurant_data_platform",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    description="Batch pipeline for sales and inventory"
) as dag:

    # =========================
    # LOAD SALES CSV
    # =========================

    load_sales_staging = BashOperator(
        task_id="load_sales_staging",
        bash_command="python batch/load_sales_bucket.py",
        cwd=str(DAG_FOLDER)
    )

    # =========================
    # LOAD INVENTORY CSV
    # =========================

    load_inventory_staging = BashOperator(
        task_id="load_inventory_staging",
        bash_command="python batch/load_inventory_bucket.py",
        cwd=str(DAG_FOLDER)
    )

    # =========================
    # RUN SALES INCREMENTAL
    # =========================

    incremental_sales = BashOperator(
        task_id="incremental_sales",
        bash_command=(
            "bq query "
            "--use_legacy_sql=false "
            "< sql/incremental.sql"
        ),
        cwd=str(DAG_FOLDER)
    )

    # =========================
    # RUN INVENTORY INCREMENTAL
    # =========================

    incremental_inventory = BashOperator(
        task_id="incremental_inventory",
        bash_command=(
            "bq query "
            "--use_legacy_sql=false "
            "< sql/incremental_inventory.sql"
        ),
        cwd=str(DAG_FOLDER)
    )

    # =========================
    # POPULATE STAR SCHEMA
    # =========================

    populate_star_schema = BashOperator(
        task_id="populate_star_schema",
        bash_command=(
            "bq query "
            "--use_legacy_sql=false "
            "< sql/populate_star_schema.sql"
        ),
        cwd=str(DAG_FOLDER)
    )

    # =========================
    # ANALYTICS VIEWS
    # =========================

    analytics_views = BashOperator(
        task_id="analytics_views",
        bash_command=(
            "bq query "
            "--use_legacy_sql=false "
            "< sql/analytics_views.sql"
        ),
        cwd=str(DAG_FOLDER)
    )

    # =========================
    # PIPELINE FLOW
    # =========================

    load_sales_staging >> incremental_sales

    load_inventory_staging >> incremental_inventory

    [
        incremental_sales,
        incremental_inventory
    ] >> populate_star_schema >> analytics_views
