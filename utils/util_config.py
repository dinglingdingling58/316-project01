import os
from typing import Set, Dict, Any

INPUT_DIR = os.path.join(os.getcwd(), 'source_data')
OUTPUT_DIR = os.path.join(os.getcwd(), 'output_build')
REPORT_FILE = 'analysis-report.txt'
PROTECTED_FILE = '.do_not_touch.cfg'

SUPPORTED_EXTENSIONS: Set[str] = {'.md', '.py', '.txt', '.rst', '.html'}

MD_HEADING_PATTERNS: Dict[int, str] = {
    1: r'^#\s+(.+)$',
    2: r'^##\s+(.+)$',
    3: r'^###\s+(.+)$',
    4: r'^####\s+(.+)$',
}

SINGLE_LETTER_VARS: Set[str] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}

PY_DEF_PATTERN = r'^\s*def\s+(\w+)\s*\('
PY_CLASS_PATTERN = r'^\s*class\s+(\w+)\s*[:\(]'
PY_VAR_PATTERN = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='

ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin-1']


def read_protected_config() -> str:
    content = ''
    try:
        if os.path.exists(PROTECTED_FILE):
            with open(PROTECTED_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
    except Exception:
        pass
    return content
