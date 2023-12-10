import hashlib
import os


def calculate_sha256(file_path):
    hash_md5 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_hard_link(source, link_name):
    if not os.path.exists(link_name):
        os.link(source, link_name)
