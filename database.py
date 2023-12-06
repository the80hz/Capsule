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
        c.execute('''CREATE TABLE IF NOT EXISTS file_hashes
                     (path TEXT PRIMARY KEY, hash TEXT)''')
    except Exception as e:
        print(e)


def upsert_file_hash(conn, file_path, file_hash):
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO file_hashes(path, hash)
                     VALUES(?, ?)
                     ON CONFLICT(path)
                     DO UPDATE SET hash=excluded.hash;''', (file_path, file_hash))
        conn.commit()
    except Exception as e:
        print(e)


def get_file_hash(conn, file_path):
    try:
        c = conn.cursor()
        c.execute("SELECT hash FROM file_hashes WHERE path=?", (file_path,))
        return c.fetchone()
    except Exception as e:
        print(e)
        return None
