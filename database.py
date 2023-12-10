import sqlite3


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn


def create_table(conn):
    try:
        c = conn.cursor()
        c.execute('''
                CREATE TABLE IF NOT EXISTS file_data
                (path TEXT PRIMARY KEY, size INTEGER, last_modified REAL, hash TEXT, backup_path TEXT)
            ''')
    except Exception as e:
        print(e)


def insert_file_data(conn, orig_path, size, last_modified, file_hash, backup_path):
    try:
        c = conn.cursor()
        c.execute('''
                INSERT OR REPLACE INTO file_data (path, size, last_modified, hash, backup_path) 
                VALUES (?, ?, ?, ?, ?)
            ''', (orig_path, size, last_modified, file_hash, backup_path))
        conn.commit()
    except Exception as e:
        print(e)


def get_file_data(conn, file_hash=None, size=None, last_modified=None):
    try:
        c = conn.cursor()
        if file_hash:
            c.execute("SELECT path, size, last_modified, backup_path FROM file_data WHERE hash=?", (file_hash,))
        elif size is not None and last_modified is not None:
            c.execute("SELECT path, hash, backup_path FROM file_data WHERE size=? AND last_modified=?",
                      (size, last_modified))
        else:
            return None
        return c.fetchone()
    except Exception as e:
        print(e)
