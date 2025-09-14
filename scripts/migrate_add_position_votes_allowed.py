"""
Add `votes_allowed` column to `position` table for SQLite.
Usage:
    python scripts\migrate_add_position_votes_allowed.py

This script:
 - backs up instance/app.db to instance/app.db.bak
 - checks if `votes_allowed` exists on `position`
 - if not, runs ALTER TABLE position ADD COLUMN votes_allowed INTEGER DEFAULT 1
 - leaves existing rows with value 1

Note: SQLite supports ADD COLUMN when the new column has no NOT NULL constraint without a default value.
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

cur.execute("PRAGMA table_info(position);")
cols = cur.fetchall()
col_names = [c[1] for c in cols]
print('position table columns:', col_names)

if 'votes_allowed' in col_names:
    print('Column votes_allowed already exists on position; nothing to do.')
    conn.close()
    raise SystemExit(0)

print('Adding votes_allowed column to position table...')
# add column with default 1
cur.execute('ALTER TABLE position ADD COLUMN votes_allowed INTEGER DEFAULT 1;')
conn.commit()
conn.close()
print('Migration complete. Database backed up at', BACKUP_PATH)
