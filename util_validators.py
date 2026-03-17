# -*- coding: utf-8 -*-
"""
验证工具模块 - 路径、文件名合法性检查等小工具函数
"""
import os
import re
from typing import List, Tuple, Optional


def is_valid_path(path: str) -> bool:
    """检查路径是否有效"""
    if not path or not isinstance(path, str):
        return False
    try:
        return os.path.exists(path)
    except Exception:
        return False


def is_directory(path: str) -> bool:
    """检查路径是否为目录"""
    if not is_valid_path(path):
        return False
    try:
        return os.path.isdir(path)
    except Exception:
        return False


def is_file(path: str) -> bool:
    """检查路径是否为文件"""
    if not is_valid_path(path):
        return False
    try:
        return os.path.isfile(path)
    except Exception:
        return False


def is_readable_file(path: str) -> bool:
    """检查文件是否可读"""
    if not is_file(path):
        return False
    try:
        return os.access(path, os.R_OK)
    except Exception:
        return False


def is_writable_dir(path: str) -> bool:
    """检查目录是否可写"""
    if not is_directory(path):
        return False
    try:
        return os.access(path, os.W_OK)
    except Exception:
        return False


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（包含点号）"""
    if not filename or not isinstance(filename, str):
        return ""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def is_supported_file(filename: str, supported_extensions: List[str]) -> bool:
    """检查文件是否为支持的类型"""
    if not filename:
        return False
    ext = get_file_extension(filename)
    return ext in supported_extensions


def is_valid_filename(filename: str) -> bool:
    """检查文件名是否合法（不包含非法字符）"""
    if not filename or not isinstance(filename, str):
        return False
    
    illegal_chars = r'[<>:"|?*\x00-\x1f]'
    if re.search(illegal_chars, filename):
        return False
    
    if filename.startswith(' ') or filename.endswith(' '):
        return False
    
    if filename in ('.', '..'):
        return False
    
    return True


def normalize_path(path: str) -> str:
    """规范化路径"""
    if not path:
        return ""
    try:
        return os.path.normpath(path)
    except Exception:
        return path


def join_paths(*paths: str) -> str:
    """安全地连接多个路径"""
    try:
        return os.path.join(*paths)
    except Exception:
        return paths[-1] if paths else ""


def get_relative_path(full_path: str, base_path: str) -> str:
    """获取相对于基准路径的相对路径"""
    try:
        return os.path.relpath(full_path, base_path)
    except Exception:
        return full_path


def ensure_dir_exists(dir_path: str) -> Tuple[bool, Optional[str]]:
    """确保目录存在，不存在则创建"""
    if not dir_path:
        return False, "目录路径为空"
    
    try:
        if os.path.exists(dir_path):
            if not os.path.isdir(dir_path):
                return False, f"路径存在但不是目录: {dir_path}"
            return True, None
        
        os.makedirs(dir_path, exist_ok=True)
        return True, None
    except Exception as e:
        return False, f"创建目录失败: {str(e)}"


def is_hidden_file(filename: str) -> bool:
    """检查是否为隐藏文件（Unix/Linux以.开头，Windows文件属性）"""
    if not filename:
        return False
    
    basename = os.path.basename(filename)
    
    if basename.startswith('.'):
        return True
    
    return False


def is_hidden_dir(dir_path: str) -> bool:
    """检查是否为隐藏目录"""
    basename = os.path.basename(dir_path)
    return basename.startswith('.')


def validate_file_size(path: str, max_size_mb: float = 10.0) -> Tuple[bool, Optional[str]]:
    """验证文件大小是否在合理范围内"""
    if not is_file(path):
        return False, "文件不存在"
    
    try:
        size_bytes = os.path.getsize(path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if size_bytes > max_size_bytes:
            return False, f"文件过大: {size_bytes / (1024 * 1024):.2f}MB"
        
        return True, None
    except Exception as e:
        return False, f"无法获取文件大小: {str(e)}"


def sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    if not filename:
        return ""
    
    illegal_chars = r'[<>:"|?*\x00-\x1f]'
    sanitized = re.sub(illegal_chars, '_', filename)
    
    sanitized = sanitized.strip()
    
    if sanitized in ('.', '..'):
        sanitized = 'file'
    
    return sanitized


def split_path_components(path: str) -> List[str]:
    """将路径分割为各个组件"""
    if not path:
        return []
    
    normalized = normalize_path(path)
    components = []
    
    while True:
        head, tail = os.path.split(normalized)
        if not tail:
            break
        components.insert(0, tail)
        normalized = head
        if not head or head == os.path.sep:
            break
    
    return components
