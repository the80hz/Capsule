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
        # Изменение структуры таблицы
        c.execute('''
            CREATE TABLE IF NOT EXISTS file_data
            (path TEXT PRIMARY KEY, size INTEGER, last_modified REAL, hash TEXT)
        ''')
    except Exception as e:
        print(e)


def insert_file_data(conn, file_path, size, last_modified, file_hash):
    try:
        c = conn.cursor()
        # Вставка данных файла
        c.execute('''
            INSERT INTO file_data (path, size, last_modified, hash) 
            VALUES (?, ?, ?, ?)
        ''', (file_path, size, last_modified, file_hash))
        conn.commit()
    except Exception as e:
        print(e)


def get_file_data(conn, file_path):
    try:
        c = conn.cursor()
        # Получение данных файла
        c.execute("SELECT size, last_modified, hash FROM file_data WHERE path=?", (file_path,))
        return c.fetchone()
    except Exception as e:
        print(e)
        return None
