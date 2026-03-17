import os
from typing import List, Dict, Any

from utils.util_config import SUPPORTED_EXTENSIONS
from utils.util_validators import is_supported_extension


def scan_directory(input_dir: str) -> List[Dict[str, Any]]:
    files_info = []
    try:
        for root, dirs, files in os.walk(input_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                if is_supported_extension(file_path):
                    try:
                        file_info = {
                            'path': file_path,
                            'relative_path': os.path.relpath(file_path, input_dir),
                            'filename': filename,
                            'extension': os.path.splitext(filename)[1].lower(),
                            'size': os.path.getsize(file_path)
                        }
                        files_info.append(file_info)
                    except Exception:
                        continue
    except Exception:
        pass
    return files_info


def get_file_type_stats(files_info: List[Dict[str, Any]]) -> Dict[str, int]:
    stats = {}
    for info in files_info:
        ext = info['extension']
        stats[ext] = stats.get(ext, 0) + 1
    return stats


def read_file_content(file_path: str) -> str:
    from utils.util_config import ENCODINGS
    for encoding in ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''
