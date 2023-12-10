import os
import shutil
from datetime import datetime
from file_utils import calculate_hash, create_hard_link
from database import create_connection, insert_file_data, get_file_data


def backup_files(source, destination, db_file):
    # Создаем новое соединение с базой данных
    db_conn = create_connection(db_file)

    # Функция для рекурсивного копирования файлов и папок
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
            existing_data = get_file_data(db_conn, src)

            if file_size < 500 * 1024 * 1024:  # Для файлов < 500 МБ
                file_hash = calculate_hash(src)
                if not existing_data or existing_data[2] != file_hash:
                    shutil.copy(src, dst)
                    insert_file_data(db_conn, src, file_size, last_modified, file_hash)
                else:
                    create_hard_link(src, dst)
            else:  # Для файлов >= 500 МБ
                if not existing_data or existing_data[0] != file_size or existing_data[1] != last_modified:
                    shutil.copy(src, dst)
                    file_hash = calculate_hash(src)  # Вычисляем хеш для записи в БД
                    insert_file_data(db_conn, src, file_size, last_modified, file_hash)
                else:
                    create_hard_link(src, dst)

    # Получаем текущее время для создания уникальной папки версии
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_path = os.path.join(destination, timestamp)

    # Рекурсивное копирование из исходной директории в целевую
    recursive_copy(source, version_path)

    # Закрываем соединение с базой данных
    db_conn.close()
