import hashlib
import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def calculate_sha256(file_path: str, block_size: int = 4096) -> Optional[str]:
    """
    Вычисляет SHA-256 хеш файла.

    :param file_path: Путь к файлу
    :param block_size: Размер блока для чтения файла
    :return: Хеш SHA-256 файла или None в случае ошибки
    """
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(block_size), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logging.error(f"Ошибка при вычислении SHA-256 для файла {file_path}: {e}")
        return None


def create_hard_link(source: str, link_name: str) -> None:
    """
    Создает жесткую ссылку.

    :param source: Исходный файл
    :param link_name: Имя жесткой ссылки
    """
    try:
        if not os.path.exists(link_name):
            os.link(source, link_name)
        else:
            logging.warning(f"Жесткая ссылка уже существует: {link_name}")
    except Exception as e:
        logging.error(f"Ошибка при создании жесткой ссылки {link_name} из {source}: {e}")
