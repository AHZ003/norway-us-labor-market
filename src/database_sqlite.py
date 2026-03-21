"""
database_sqlite.py
------------------
Builds a lightweight SQLite database from the processed CSVs and
provides a connection helper used by the dashboard.

SQLite ships with Python so this works locally and on Streamlit Cloud
without any external database setup.
"""

import sqlite3
import pandas as pd
import os
import tempfile

# /tmp works on Streamlit Cloud; locally it's just the system temp dir
DB_PATH = os.path.join(tempfile.gettempdir(), "labor_market.db")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def build_db():
    conn = sqlite3.connect(DB_PATH)
    for table, filename in [
        ("unemployment", "unemployment_clean.csv"),
        ("wages",        "wages_clean.csv"),
        ("employment",   "employment_clean.csv"),
    ]:
        path = os.path.join(PROCESSED_DIR, filename)
        if os.path.exists(path):
            pd.read_csv(path).to_sql(table, conn, if_exists="replace", index=False)
    conn.close()


def get_conn():
    if not os.path.exists(DB_PATH):
        build_db()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def query(conn, sql):
    return pd.read_sql_query(sql, conn)
