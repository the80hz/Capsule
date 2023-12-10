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


def get_file_data(conn, file_hash=None, size=None, last_modified=None):
    c = conn.cursor()
    if file_hash:
        # Получение данных файла по его хешу
        c.execute("SELECT path, size, last_modified FROM file_data WHERE hash=?", (file_hash,))
    elif size is not None and last_modified is not None:
        # Получение данных файла по его размеру и дате последнего изменения
        c.execute("SELECT path, hash FROM file_data WHERE size=? AND last_modified=?", (size, last_modified))
    else:
        # Возвращаем None, если не предоставлены ни хеш, ни размер с датой
        return None
    return c.fetchone()
