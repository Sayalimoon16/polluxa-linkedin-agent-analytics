import sqlite3
import csv
import os

DB_PATH = "data/polluxa_analytics.db"
OUTPUT_DIR = "powerbi_data"

conn = sqlite3.connect(DB_PATH)
os.makedirs(OUTPUT_DIR, exist_ok=True)

tables = [
    row[0]
    for row in conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
]

print("TABLES FOUND:")
for table in tables:
    print("-", table)

for table in tables:
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    output_file = os.path.join(
        OUTPUT_DIR,
        table + ".csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"EXPORTED: {output_file} ({len(rows)} rows)")

conn.close()

print()
print("POWER BI CSV EXPORT COMPLETE")