"""
配置模块 - 存储常量、支持的后缀列表和配置读取功能。

路径约束：
- 输入目录： ./source_data/
- 输出目录： ./output_build/
- 禁止在 ./source_data/ 目录下创建、修改、删除、重命名任何文件
- 存在名为 .do_not_touch.cfg 的文件（用于标记不可碰目录），程序应读取它但绝不修改它
"""

import os
from typing import List, Set, Dict, Any


# =============================================================================
# 路径常量
# =============================================================================

INPUT_DIRECTORY: str = './source_data/'
OUTPUT_DIRECTORY: str = './output_build/'
REPORT_FILENAME: str = 'analysis-report.txt'
PROTECTED_MARKER_FILE: str = '.do_not_touch.cfg'


# =============================================================================
# 支持的文件扩展名
# =============================================================================

SUPPORTED_EXTENSIONS: Set[str] = {
    '.md',   # Markdown 文件
    '.py',   # Python 源代码
    '.txt',  # 纯文本文件
    '.rst',  # reStructuredText 文件
    '.html', # HTML 文件
}


# =============================================================================
# Markdown 相关常量
# =============================================================================

MARKDOWN_HEADER_LEVELS: int = 4  # 支持 H1-H4
MARKDOWN_HEADER_PATTERN: str = r'^(#{1,4})\s+(.+)$'
MARKDOWN_CODE_BLOCK_PATTERN: str = r'```[\s\S]*?```'
MARKDOWN_INLINE_CODE_PATTERN: str = r'`[^`]+`'
MARKDOWN_LINK_PATTERN: str = r'\[([^\]]+)\]\(([^)]+)\)'
MARKDOWN_TABLE_PATTERN: str = r'\|[^\n]+\|[^\n]*\|[\s\S]*?(?=\n\n|\n#|$)'


# =============================================================================
# Python 静态检查相关常量
# =============================================================================

PYTHON_SINGLE_LETTER_VARS: Set[str] = {
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
    'u', 'v', 'w', 'x', 'y', 'z',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z',
}

PYTHON_FUNCTION_PATTERN: str = r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
PYTHON_CLASS_PATTERN: str = r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
PYTHON_VARIABLE_ASSIGNMENT_PATTERN: str = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='


# =============================================================================
# HTML 相关常量
# =============================================================================

HTML_TITLE_PATTERN: str = r'<title[^>]*>([^<]*)</title>'
HTML_HEADER_PATTERNS: List[str] = [
    r'<h1[^>]*>([^<]*)</h1>',
    r'<h2[^>]*>([^<]*)</h2>',
    r'<h3[^>]*>([^<]*)</h3>',
    r'<h4[^>]*>([^<]*)</h4>',
]
HTML_LINK_PATTERN: str = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
HTML_TABLE_PATTERN: str = r'<table[\s\S]*?</table>'


# =============================================================================
# 配置读取功能
# =============================================================================

def read_protected_marker() -> Dict[str, Any]:
    """
    读取 .do_not_touch.cfg 配置文件。
    
    该文件用于标记不可碰目录，程序应读取它但绝不修改它。
    
    Returns:
        包含配置信息的字典
    """
    config: Dict[str, Any] = {
        'protected_paths': [],
        'read_only': True,
        'marker_exists': False,
    }
    
    marker_path = os.path.join(INPUT_DIRECTORY, PROTECTED_MARKER_FILE)
    
    if not os.path.exists(marker_path):
        return config
    
    config['marker_exists'] = True
    
    try:
        with open(marker_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('protected:'):
                    path = line[len('protected:'):].strip()
                    if path:
                        config['protected_paths'].append(path)
                elif line.startswith('read_only:'):
                    value = line[len('read_only:'):].strip().lower()
                    config['read_only'] = value in ('true', 'yes', '1')
    except Exception:
        # 如果读取失败，返回默认配置
        pass
    
    return config


def get_output_report_path() -> str:
    """
    获取输出报告的完整路径。
    
    Returns:
        报告文件的完整路径
    """
    return os.path.join(OUTPUT_DIRECTORY, REPORT_FILENAME)


def ensure_output_directory() -> bool:
    """
    确保输出目录存在。
    
    Returns:
        如果目录存在或创建成功返回 True，否则返回 False
    """
    try:
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        return True
    except Exception:
        return False
