import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

columns = [
    ("role", "varchar(30) DEFAULT 'citizen'"),
    ("phone_number", "varchar(15) NULL"),
    ("preferred_language", "varchar(10) DEFAULT 'en'"),
    ("is_verified", "bool DEFAULT 0"),
    ("district_id", "bigint NULL"),
    ("created_at", "datetime NULL")
]

cur.execute("PRAGMA table_info(accounts_user)")
existing_cols = {row[1] for row in cur.fetchall()}

for col_name, col_def in columns:
    if col_name not in existing_cols:
        cur.execute(f"ALTER TABLE accounts_user ADD COLUMN {col_name} {col_def}")
        print(f"Added column {col_name}")
    else:
        print(f"Column {col_name} already exists.")

conn.commit()
conn.close()
print("Done fixing SQLite accounts_user schema.")
