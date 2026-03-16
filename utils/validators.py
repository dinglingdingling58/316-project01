"""
验证工具模块 - 提供路径、文件名合法性检查等小工具函数。

路径约束：
- 输入目录： ./source_data/
- 输出目录： ./output_build/
- 禁止在 ./source_data/ 目录下创建、修改、删除、重命名任何文件
"""

import os
import re
from typing import Optional, Tuple, List


# =============================================================================
# 文件名验证
# =============================================================================

def is_valid_module_filename(filename: str) -> bool:
    """
    验证 Python 模块文件名是否符合命名规范。
    
    规范：
    - 必须使用小写 + 下划线风格
    - 必须以以下前缀之一开头：core_, scan_, parse_, report_, util_
    
    Args:
        filename: 要验证的文件名
        
    Returns:
        如果文件名符合规范返回 True，否则返回 False
    """
    valid_prefixes = ('core_', 'scan_', 'parse_', 'report_', 'util_')
    
    # 移除 .py 扩展名
    name = filename
    if name.endswith('.py'):
        name = name[:-3]
    
    # 检查前缀
    if not any(name.startswith(prefix) for prefix in valid_prefixes):
        return False
    
    # 检查是否为小写 + 下划线风格
    if not re.match(r'^[a-z][a-z0-9_]*$', name):
        return False
    
    return True


def validate_source_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    验证源文件是否可以被处理。
    
    Args:
        filename: 要验证的文件名
        
    Returns:
        (是否有效, 错误信息)
    """
    if not filename:
        return False, "文件名为空"
    
    # 检查是否有扩展名
    if '.' not in filename:
        return False, "文件没有扩展名"
    
    # 获取扩展名
    ext = os.path.splitext(filename)[1].lower()
    
    from utils.config import SUPPORTED_EXTENSIONS
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"不支持的文件类型: {ext}"
    
    return True, None


# =============================================================================
# 路径验证
# =============================================================================

def is_within_input_directory(path: str, input_dir: str = './source_data/') -> bool:
    """
    检查路径是否在输入目录内。
    
    Args:
        path: 要检查的路径
        input_dir: 输入目录路径
        
    Returns:
        如果路径在输入目录内返回 True，否则返回 False
    """
    abs_path = os.path.abspath(path)
    abs_input = os.path.abspath(input_dir)
    
    # 确保以分隔符结尾，避免部分匹配
    if not abs_input.endswith(os.sep):
        abs_input += os.sep
    
    return abs_path.startswith(abs_input)


def is_safe_to_write(path: str, input_dir: str = './source_data/') -> bool:
    """
    检查是否可以安全地写入文件（不在受保护的输入目录内）。
    
    Args:
        path: 要检查的路径
        input_dir: 输入目录路径
        
    Returns:
        如果可以安全写入返回 True，否则返回 False
    """
    return not is_within_input_directory(path, input_dir)


def normalize_path(path: str) -> str:
    """
    规范化路径，使用统一的格式。
    
    Args:
        path: 原始路径
        
    Returns:
        规范化后的路径
    """
    return os.path.normpath(path)


def get_relative_path(full_path: str, base_dir: str) -> str:
    """
    获取相对于基目录的相对路径。
    
    Args:
        full_path: 完整路径
        base_dir: 基目录
        
    Returns:
        相对路径
    """
    abs_full = os.path.abspath(full_path)
    abs_base = os.path.abspath(base_dir)
    
    try:
        return os.path.relpath(abs_full, abs_base)
    except ValueError:
        # Windows 上不同驱动器可能导致错误
        return full_path


# =============================================================================
# 内容验证
# =============================================================================

def is_binary_file(filepath: str, sample_size: int = 8192) -> bool:
    """
    检测文件是否为二进制文件。
    
    Args:
        filepath: 文件路径
        sample_size: 采样字节数
        
    Returns:
        如果是二进制文件返回 True，否则返回 False
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(sample_size)
            if not chunk:
                return False
            
            # 检查空字节（二进制文件的常见特征）
            if b'\x00' in chunk:
                return True
            
            # 检查可打印字符比例
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            non_text = chunk.translate(None, text_chars)
            
            # 如果非文本字符超过 30%，认为是二进制文件
            return len(non_text) / len(chunk) > 0.30
    except Exception:
        return True


def is_protected_path(path: str, protected_paths: List[str], input_dir: str = './source_data/') -> bool:
    """
    检查路径是否受保护（不应被修改）。
    
    Args:
        path: 要检查的路径
        protected_paths: 受保护路径列表
        input_dir: 输入目录
        
    Returns:
        如果路径受保护返回 True，否则返回 False
    """
    abs_path = os.path.abspath(path)
    abs_input = os.path.abspath(input_dir)
    
    for protected in protected_paths:
        abs_protected = os.path.abspath(os.path.join(abs_input, protected))
        if abs_path == abs_protected or abs_path.startswith(abs_protected + os.sep):
            return True
    
    return False


# =============================================================================
# 统计信息验证
# =============================================================================

def clamp_value(value: int, min_val: int = 0, max_val: int = 999999) -> int:
    """
    将数值限制在有效范围内。
    
    Args:
        value: 原始值
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        限制后的值
    """
    return max(min_val, min(value, max_val))


def format_count(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    根据数量格式化名词。
    
    Args:
        count: 数量
        singular: 单数形式
        plural: 复数形式（可选，默认为单数+s）
        
    Returns:
        格式化后的字符串
    """
    if plural is None:
        plural = singular + 's'
    
    word = singular if count == 1 else plural
    return f"{count} {word}"
