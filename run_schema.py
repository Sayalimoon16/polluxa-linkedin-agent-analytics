import sqlite3

db = "data/polluxa_analytics.db"
schema_file = "sql/schema.sql"

conn = sqlite3.connect(db)

with open(schema_file, "r", encoding="utf-8") as f:
    schema = f.read()

conn.executescript(schema)
conn.commit()

print("Part 3 schema created successfully")

tables = conn.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' ORDER BY name"
).fetchall()

print("Tables:")
for table in tables:
    print("-", table[0])

conn.close()