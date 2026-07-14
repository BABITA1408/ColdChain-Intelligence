"""
Ingestion step: loads raw CSVs into DuckDB as a 'raw' schema.
In a real enterprise setup this is what Azure Data Factory / Fivetran / Airbyte
would do (land raw files into the warehouse). Here we do it directly since
DuckDB can read CSVs natively - free, fast, zero infra.

Uses relative/portable paths so this works identically on any machine or
when deployed to Streamlit Community Cloud.
"""
import os
import duckdb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DB_PATH = os.environ.get("MELT_RISK_DB_PATH", os.path.join(PROJECT_ROOT, "warehouse.duckdb"))
RAW_DIR = os.path.join(SCRIPT_DIR, "raw")

con = duckdb.connect(DB_PATH)
con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

tables = ["products", "warehouses", "orders", "inventory", "shipments"]
for t in tables:
    csv_path = os.path.join(RAW_DIR, f"{t}.csv")
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.{t} AS
        SELECT * FROM read_csv_auto('{csv_path}');
    """)
    count = con.execute(f"SELECT COUNT(*) FROM raw.{t}").fetchone()[0]
    print(f"Loaded raw.{t}: {count} rows")

con.close()
