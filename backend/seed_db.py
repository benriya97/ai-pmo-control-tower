# =========================================================
# seed_db.py — ONE-TIME script to load CSV data into SQLite
# Run this once: python seed_db.py
# Safe to re-run — it recreates the tables from the CSVs each time.
# =========================================================

import pandas as pd
import sqlite3
import os

# Same path pattern as main.py — absolute paths so it works anywhere.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../data/pmo.db")   # the SQLite file we're creating

# Read the existing CSVs (the data we already have).
tasks = pd.read_csv(os.path.join(BASE_DIR, "../data/tasks.csv"))
resources = pd.read_csv(os.path.join(BASE_DIR, "../data/resources.csv"))

# Open a connection to the SQLite file. If pmo.db doesn't exist, it's created.
conn = sqlite3.connect(DB_PATH)

# Write each DataFrame into a table of the same name.
# if_exists="replace" = drop the table if it exists, then recreate it.
# index=False = don't write pandas' row-number index as a column.
tasks.to_sql("tasks", conn, if_exists="replace", index=False)
resources.to_sql("resources", conn, if_exists="replace", index=False)

conn.close()

print(f"✅ Database seeded at {DB_PATH}")
print(f"   - {len(tasks)} tasks, {len(resources)} resources")