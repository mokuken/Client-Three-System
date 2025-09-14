"""
Add `election_id` column to `candidate` table for SQLite.
Usage:
    python scripts\migrate_add_candidate_election.py

This script:
 - backs up instance/app.db to instance/app.db.bak
 - checks if `election_id` exists on `candidate`
 - if not, runs ALTER TABLE candidate ADD COLUMN election_id INTEGER
 - leaves existing rows NULL (column is nullable)

Note: SQLite supports ADD COLUMN when the new column has no NOT NULL constraint without a default.
"""
import os
import shutil
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
BACKUP_PATH = DB_PATH + '.bak'

if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    raise SystemExit(1)

print('Backing up database to', BACKUP_PATH)
shutil.copy2(DB_PATH, BACKUP_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(candidate);")
cols = cur.fetchall()
col_names = [c[1] for c in cols]
print('candidate table columns:', col_names)

if 'election_id' in col_names:
    print('Column election_id already exists on candidate; nothing to do.')
    conn.close()
    raise SystemExit(0)

print('Adding election_id column to candidate table...')
cur.execute('ALTER TABLE candidate ADD COLUMN election_id INTEGER;')
conn.commit()
conn.close()
print('Migration complete. Database backed up at', BACKUP_PATH)
