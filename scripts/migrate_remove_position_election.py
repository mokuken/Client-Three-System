"""
Migration script for SQLite to remove the `election_id` column from the `position` table.
Strategy: create a new table `position_new` with the desired schema (no election_id), copy data,
then drop old table and rename new table.

Run:
    python scripts\migrate_remove_position_election.py

This script is idempotent-safe: if the column does not exist it will exit early.
Make a backup of `instance/app.db` before running.
"""
import sqlite3
import shutil
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
BACKUP_PATH = DB_PATH + '.bak'

if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    raise SystemExit(1)

print('Backing up database to', BACKUP_PATH)
shutil.copy2(DB_PATH, BACKUP_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# check columns of position table
cur.execute("PRAGMA table_info(position);")
cols = cur.fetchall()
col_names = [c[1] for c in cols]
print('position table columns:', col_names)

if 'election_id' not in col_names:
    print('No election_id column found in position table; nothing to do.')
    conn.close()
    raise SystemExit(0)

print('Creating new position table without election_id...')
cur.execute('''
CREATE TABLE position_new (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    max_winners INTEGER NOT NULL DEFAULT 1
);
''')

print('Copying data...')
# copy data from old table (exclude election_id)
cur.execute('INSERT INTO position_new (id, title, description, max_winners) SELECT id, title, description, max_winners FROM position;')

print('Dropping old table and renaming new table...')
cur.execute('DROP TABLE position;')
cur.execute('ALTER TABLE position_new RENAME TO position;')

conn.commit()
conn.close()
print('Migration complete. Database backed up at', BACKUP_PATH)
