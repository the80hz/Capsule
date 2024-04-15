import sqlite3
import logging
from typing import Optional, List, Tuple, Any

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
            # Таблица для данных о файлах
            c.execute('''
                CREATE TABLE IF NOT EXISTS file_data (
                    path TEXT,
                    size INTEGER,
                    last_modified REAL,
                    hash TEXT,
                    backup_path TEXT
                )
            ''')
            # Таблица для исключенных директорий
            c.execute('''
                CREATE TABLE IF NOT EXISTS excluded_directories (
                    path TEXT UNIQUE
                )
            ''')
            logging.info("Таблицы созданы успешно")
        except Exception as e:
            logging.error(f"Ошибка при создании таблиц: {e}")


def add_excluded_directory(conn: sqlite3.Connection, directory_path: str) -> None:
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO excluded_directories (path) VALUES (?)
        ''', (directory_path,))
        conn.commit()
        logging.info(f"Директория {directory_path} добавлена в список исключений")
    except Exception as e:
        logging.error(f"Ошибка при добавлении исключенной директории: {e}")


def get_excluded_directories(conn: sqlite3.Connection) -> List[str]:
    try:
        c = conn.cursor()
        c.execute("SELECT path FROM excluded_directories")
        rows = c.fetchall()
        return [row[0] for row in rows]  # Возвращаем список путей
    except Exception as e:
        logging.error(f"Ошибка при получении списка исключенных директорий: {e}")
        return []


def remove_excluded_directory(conn: sqlite3.Connection, directory_path: str) -> None:
    try:
        c = conn.cursor()
        c.execute('''
            DELETE FROM excluded_directories WHERE path=?
        ''', (directory_path,))
        conn.commit()
        logging.info(f"Директория {directory_path} удалена из списка исключений")
    except Exception as e:
        logging.error(f"Ошибка при удалении исключенной директории: {e}")


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
    try:
        c = conn.cursor()
        c.execute("SELECT path, hash FROM file_data WHERE path=? AND hash=?", (orig_path, file_hash))
        existing_record = c.fetchone()

        if existing_record:
            c.execute('''
                UPDATE file_data
                SET size = ?, last_modified = ?, backup_path = ?
                WHERE path = ? AND hash = ?
            ''', (size, last_modified, backup_path, orig_path, file_hash))
        else:
            c.execute('''
                INSERT INTO file_data (path, size, last_modified, hash, backup_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (orig_path, size, last_modified, file_hash, backup_path))

        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при вставке или обновлении данных: {e}")


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
