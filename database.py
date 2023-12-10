import sqlite3
import logging
from typing import Optional, Tuple, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_connection(db_file: str) -> Optional[sqlite3.Connection]:
    """
    Создает соединение с базой данных SQLite.

    :param db_file: Путь к файлу базы данных
    :return: Объект соединения или None в случае ошибки
    """
    try:
        return sqlite3.connect(db_file)
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None


def create_table(conn: sqlite3.Connection) -> None:
    """
    Создает таблицу в базе данных.

    :param conn: Объект соединения с базой данных
    """
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


def insert_file_data(conn: sqlite3.Connection, orig_path: str, size: int,
                     last_modified: float, file_hash: str, backup_path: str) -> None:
    """
    Вставляет или обновляет данные о файле в базе данных.

    :param conn: Объект соединения с базой данных
    :param orig_path: Оригинальный путь к файлу
    :param size: Размер файла
    :param last_modified: Время последнего изменения файла
    :param file_hash: Хеш файла
    :param backup_path: Путь к резервной копии файла
    """
    with conn:
        try:
            c = conn.cursor()
            c.execute('''
                    INSERT OR REPLACE INTO file_data (path, size, last_modified, hash, backup_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (orig_path, size, last_modified, file_hash, backup_path))
        except Exception as e:
            logging.error(f"Ошибка при вставке данных: {e}")


def get_file_data(conn: sqlite3.Connection, file_hash: Optional[str] = None,
                  size: Optional[int] = None, last_modified: Optional[float] = None) -> Optional[Tuple[Any, ...]]:
    """
    Получает данные о файле из базы данных.

    :param conn: Объект соединения с базой данных
    :param file_hash: Хеш файла (для поиска)
    :param size: Размер файла (для поиска)
    :param last_modified: Время последнего изменения файла (для поиска)
    :return: Кортеж с данными о файле или None, если данные не найдены
    """
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
