import os
import shutil
import logging
import sqlite3
from datetime import datetime

from file_utils import calculate_sha256, create_hard_link
from database import create_connection, insert_file_data, get_file_data

logging.basicConfig(filename='backup_log.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def backup_files(source: str, destination: str, db_file: str) -> None:
    """
    Выполняет процесс резервного копирования файлов из исходного пути в пункт назначения.

    :param source: Исходный путь для копирования
    :param destination: Путь назначения для сохранения копий
    :param db_file: Путь к файлу базы данных
    """
    logging.info(f"Начало копирования из {source} в {destination}")
    try:
        db_conn = create_connection(db_file)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        version_path = os.path.join(destination, timestamp)
        recursive_copy(source, version_path, db_conn)
        db_conn.close()
        logging.info(f"Копирование завершено")
    except Exception as e:
        logging.error(f"Ошибка при копировании: {e}")


def recursive_copy(src: str, dst: str, db_conn: sqlite3.Connection) -> None:
    """
    Рекурсивно копирует файлы и директории.

    :param src: Исходный путь файла или директории
    :param dst: Путь назначения
    :param db_conn: Соединение с базой данных
    """
    try:
        if os.path.isdir(src):
            if not os.path.exists(dst):
                os.makedirs(dst)
            for file in os.listdir(src):
                recursive_copy(os.path.join(src, file), os.path.join(dst, file), db_conn)
        else:
            process_file(src, dst, db_conn)
    except Exception as e:
        logging.error(f"Ошибка при обработке {src}: {e}")


def process_file(src: str, dst: str, db_conn: sqlite3.Connection) -> None:
    """
    Обрабатывает отдельный файл: копирование или создание жесткой ссылки.

    :param src: Исходный путь файла
    :param dst: Путь назначения файла
    :param db_conn: Соединение с базой данных
    """
    file_size = os.path.getsize(src)
    last_modified = os.path.getmtime(src)
    file_hash = calculate_sha256(src) if file_size < 500 * 1024 * 1024 else None

    existing_data = get_file_data(db_conn, file_hash=file_hash, size=file_size, last_modified=last_modified)

    if not existing_data:
        shutil.copy(src, dst)
        file_hash = calculate_sha256(src) if file_hash is None else file_hash
        insert_file_data(db_conn, src, file_size, last_modified, file_hash, dst)
        logging.info(f"Скопирован файл: {src}")
    else:
        file_hash = existing_data[1] if file_size >= 500 * 1024 * 1024 else file_hash
        backup_path = existing_data[2] if file_size >= 500 * 1024 * 1024 else existing_data[3]
        if os.path.exists(backup_path):
            create_hard_link(backup_path, dst)
            logging.info(f"Создана жесткая ссылка для файла: {src} -> {dst}")
        else:
            shutil.copy(src, dst)
            logging.info(f"Скопирован файл: {src}")

        insert_file_data(db_conn, src, file_size, last_modified, file_hash, dst)


if __name__ == "__main__":
    backup_files('/path/to/source', '/path/to/destination', 'database.db')
