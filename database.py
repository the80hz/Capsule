import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_connection(db_file):
    try:
        return sqlite3.connect(db_file)
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None


def create_table(conn):
    with conn:
        try:
            c = conn.cursor()
            c.execute('''
                    CREATE TABLE IF NOT EXISTS file_data (
                        path TEXT PRIMARY KEY,
                        size INTEGER,
                        last_modified REAL,
                        hash TEXT,
                        backup_path TEXT
                    )
                ''')
        except Exception as e:
            logging.error(f"Ошибка при создании таблицы: {e}")


def insert_file_data(conn, orig_path, size, last_modified, file_hash, backup_path):
    with conn:
        try:
            c = conn.cursor()
            c.execute('''
                    INSERT OR REPLACE INTO file_data (path, size, last_modified, hash, backup_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (orig_path, size, last_modified, file_hash, backup_path))
        except Exception as e:
            logging.error(f"Ошибка при вставке данных: {e}")


def get_file_data(conn, file_hash=None, size=None, last_modified=None):
    try:
        c = conn.cursor()
        if file_hash:
            c.execute("SELECT path, size, last_modified, backup_path FROM file_data WHERE hash=?", (file_hash,))
        elif size is not None and last_modified is not None:
            c.execute("SELECT path, hash, backup_path FROM file_data WHERE size=? AND last_modified=?",
                      (size, last_modified))
        else:
            logging.warning("Нет параметров для поиска данных")
            return None
        return c.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при получении данных: {e}")
        return None
