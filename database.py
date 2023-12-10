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
        # Создание таблицы с двумя отдельными полями
        c.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes
            (path TEXT, hash TEXT)
        ''')
    except Exception as e:
        print(e)


def insert_file_hash(conn, file_path, file_hash):
    try:
        c = conn.cursor()
        # Вставка новой записи без проверки конфликтов
        c.execute('''
            INSERT INTO file_hashes (path, hash) VALUES (?, ?)
        ''', (file_path, file_hash))
        conn.commit()
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


def get_file_hashes(conn, file_path):
    try:
        c = conn.cursor()
        # Получение всех записей для данного пути
        c.execute("SELECT hash FROM file_hashes WHERE path=?", (file_path,))
        return c.fetchall()
    except Exception as e:
        print(e)
        return None
