import os
import shutil
from datetime import datetime
from file_utils import calculate_md5, create_hard_link
from database import create_connection, insert_file_hash, get_file_hashes


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
            # Вычисляем MD5 хеш файла
            file_hash = calculate_md5(src)
            existing_hashes = get_file_hashes(db_conn, src)

            if existing_hashes and any(file_hash == existing_hash[0] for existing_hash in existing_hashes):
                create_hard_link(src, dst)
            else:
                shutil.copy(src, dst)
                insert_file_hash(db_conn, src, file_hash)

    # Получаем текущее время для создания уникальной папки версии
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_path = os.path.join(destination, timestamp)

    # Рекурсивное копирование из исходной директории в целевую
    recursive_copy(source, version_path)

    # Закрываем соединение с базой данных
    db_conn.close()
