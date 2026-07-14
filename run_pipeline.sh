#!/bin/bash
# Orchestrates the full data pipeline end-to-end.
# In a production setup, each of these steps would be a task in Airflow / Azure Data
# Factory, scheduled on a cadence. Here we run them sequentially with one command -
# same logical DAG, zero infra.
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
export MELT_RISK_DB_PATH="$PROJECT_ROOT/warehouse.duckdb"
export DBT_PROFILES_DIR="$PROJECT_ROOT/dbt_project"

echo "== Step 1/4: Generating synthetic cold-chain data =="
cd "$(dirname "$0")/data"
python3 generate_data.py

echo ""
echo "== Step 2/4: Loading raw data into DuckDB warehouse =="
python3 load_to_duckdb.py

echo ""
echo "== Step 3/4: Running dbt transformations (staging -> marts) =="
cd ../dbt_project
dbt run

echo ""
echo "== Step 4/4: Running dbt data quality tests =="
dbt test

echo ""
echo "Pipeline complete. Warehouse ready at warehouse.duckdb"
echo "Run the app with: streamlit run app/streamlit_app.py"
