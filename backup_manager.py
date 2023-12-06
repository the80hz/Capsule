import tkinter as tk
from tkinter import filedialog
import shutil
import os
import schedule
import time
from datetime import datetime
import threading

from file_utils import calculate_md5, create_hard_link
from database import create_connection, create_table, upsert_file_hash, get_file_hash


def backup_files(source, destination, db_conn):
    # Получаем текущее время для создания уникальной папки версии
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_path = os.path.join(destination, timestamp)

    # Копирование файлов
    if not os.path.exists(version_path):
        os.makedirs(version_path)

    for file_name in os.listdir(source):
        full_file_name = os.path.join(source, file_name)

        file_hash = calculate_md5(full_file_name)
        existing_hash = get_file_hash(db_conn, full_file_name)

        if existing_hash and file_hash == existing_hash[0]:
            create_hard_link(full_file_name, os.path.join(version_path, file_name))
        else:
            shutil.copy(full_file_name, version_path)
            upsert_file_hash(db_conn, full_file_name, file_hash)
