import os
import shutil
from datetime import datetime
from file_utils import calculate_md5, create_hard_link
from database import create_connection, insert_file_hash, get_file_hashes


def backup_files(source, destination, db_file):
    # Создаем новое соединение с базой данных
    db_conn = create_connection(db_file)

    # Получаем текущее время для создания уникальной папки версии
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_path = os.path.join(destination, timestamp)

    # Создаем папку версии, если она еще не существует
    if not os.path.exists(version_path):
        os.makedirs(version_path)

    # Обрабатываем каждый файл в исходной директории
    for file_name in os.listdir(source):
        full_file_name = os.path.join(source, file_name)

        # Пропускаем, если это не файл
        if not os.path.isfile(full_file_name):
            continue

        # Вычисляем MD5 хеш файла
        file_hash = calculate_md5(full_file_name)

        # Получаем список всех хешей для данного пути файла из базы данных
        existing_hashes = get_file_hashes(db_conn, full_file_name)

        # Проверяем, существует ли уже файл с таким хешем
        if existing_hashes and any(file_hash == existing_hash[0] for existing_hash in existing_hashes):
            # Файл не изменился, создаем жесткую ссылку
            create_hard_link(full_file_name, os.path.join(version_path, file_name))
        else:
            # Файл новый или измененный, копируем его и добавляем запись в базу данных
            shutil.copy(full_file_name, version_path)
            insert_file_hash(db_conn, full_file_name, file_hash)

    # Закрываем соединение с базой данных
    db_conn.close()
