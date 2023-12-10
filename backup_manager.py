import os
import shutil
import logging
from datetime import datetime
from file_utils import calculate_sha256, create_hard_link
from database import create_connection, insert_file_data, get_file_data

# Настройка логгера
logging.basicConfig(filename='backup_log.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def backup_files(source, destination, db_file):
    logging.info(f"Начало копирования из {source} в {destination}")
    db_conn = create_connection(db_file)

    def recursive_copy(src, dst):
        if os.path.isdir(src):
            if not os.path.exists(dst):
                os.makedirs(dst)
            files = os.listdir(src)
            for file in files:
                recursive_copy(os.path.join(src, file), os.path.join(dst, file))
        else:
            file_size = os.path.getsize(src)
            last_modified = os.path.getmtime(src)

            if file_size < 500 * 1024 * 1024:  # Для файлов < 500 МБ
                file_hash = calculate_sha256(src)
                existing_data = get_file_data(db_conn, file_hash=file_hash)
                if not existing_data:
                    shutil.copy(src, dst)
                    insert_file_data(db_conn, src, file_size, last_modified, file_hash)
                    logging.info(f"Скопирован файл: {src}")
                else:
                    create_hard_link(src, dst)
                    logging.info(f"Создана жесткая ссылка для файла: {src}")
            else:  # Для файлов >= 500 МБ
                existing_data = get_file_data(db_conn, size=file_size, last_modified=last_modified)
                if not existing_data:
                    shutil.copy(src, dst)
                    file_hash = calculate_sha256(src)  # Вычисляем хеш для записи в БД
                    insert_file_data(db_conn, src, file_size, last_modified, file_hash)
                    logging.info(f"Скопирован файл: {src}")
                else:
                    create_hard_link(src, dst)
                    logging.info(f"Создана жесткая ссылка для файла: {src}")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_path = os.path.join(destination, timestamp)
    recursive_copy(source, version_path)
    db_conn.close()
    logging.info(f"Копирование завершено")
