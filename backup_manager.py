import os
import shutil
import logging
import sqlite3
from datetime import datetime

from file_utils import calculate_sha256, create_hard_link
from database import create_connection, insert_file_data, get_file_data, get_excluded_directories

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
        excluded_dirs = get_excluded_directories(db_conn)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        version_path = os.path.join(destination, timestamp)
        recursive_copy(source, version_path, db_conn, excluded_dirs)
        db_conn.close()
        logging.info(f"Копирование завершено")
    except Exception as e:
        logging.error(f"Ошибка при копировании: {e}")


def recursive_copy(src: str, dst: str, db_conn: sqlite3.Connection, excluded_dirs: list) -> None:
    """
    Рекурсивно копирует файлы и директории.

    :param src: Исходный путь файла или директории
    :param dst: Путь назначения
    :param db_conn: Соединение с базой данных
    :param excluded_dirs: Список директорий, которые следует исключить
    """
    # Проверяем, не находится ли директория в списке исключенных
    if any(os.path.abspath(src).startswith(os.path.abspath(ex_dir)) for ex_dir in excluded_dirs):
        logging.info(f"Директория {src} пропущена (находится в списке исключенных)")
        return

    try:
        if os.path.isdir(src):
            if not os.path.exists(dst):
                os.makedirs(dst)
            for file in os.listdir(src):
                recursive_copy(os.path.join(src, file), os.path.join(dst, file), db_conn, excluded_dirs)
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


def restore_backup(backup_path, orig_path):
    """
        Восстанавливает выбранную резервную копию.

        :param backup_path: Путь до папки резервной копии
        :param orig_path: Путь до оригинальной папки
    """
    print(backup_path, orig_path)
    restore_path = orig_path

    if os.path.exists(restore_path):
        # Очистка целевой директории перед восстановлением
        for filename in os.listdir(restore_path):
            file_path = os.path.join(restore_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    # Копирование файлов из резервной копии
    for filename in os.listdir(backup_path):
        src_path = os.path.join(backup_path, filename)
        dst_path = os.path.join(restore_path, filename)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

    logging.info(f"Восстановление из {backup_path} в {restore_path} завершено.")
