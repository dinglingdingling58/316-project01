import os
from typing import Optional

from .util_config import SUPPORTED_EXTENSIONS


def is_supported_extension(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path.lower())
    return ext in SUPPORTED_EXTENSIONS


def is_valid_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        return False
    return True


def is_readable_file(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore'):
            pass
        return True
    except Exception:
        return False


def get_file_size(file_path: str) -> Optional[int]:
    try:
        return os.path.getsize(file_path)
    except Exception:
        return None


def is_directory(path: str) -> bool:
    return os.path.isdir(path)


def validate_input_directory(input_dir: str) -> bool:
    if not os.path.exists(input_dir):
        return False
    if not os.path.isdir(input_dir):
        return False
    return True
