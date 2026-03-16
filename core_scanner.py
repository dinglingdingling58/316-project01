# -*- coding: utf-8 -*-
"""
核心扫描模块 - 文件系统遍历、类型识别、文件过滤
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from utils.config import Config
from utils.validators import (
    is_directory, is_readable_file, is_supported_file,
    is_hidden_file, is_hidden_dir, get_file_extension,
    get_relative_path, normalize_path
)


@dataclass
class FileInfo:
    """文件信息数据类"""
    path: str
    relative_path: str
    filename: str
    extension: str
    file_type: str
    size_bytes: int
    error: Optional[str] = None


@dataclass
class ScanResult:
    """扫描结果数据类"""
    files: List[FileInfo] = field(default_factory=list)
    total_files: int = 0
    total_size: int = 0
    errors: List[str] = field(default_factory=list)
    skipped_dirs: List[str] = field(default_factory=list)


class FileScanner:
    """文件扫描器 - 负责递归扫描目录并收集文件信息"""
    
    def __init__(self, config: Config):
        self._config = config
        self._result = ScanResult()
    
    def scan(self) -> ScanResult:
        """执行扫描"""
        input_dir = self._config.input_dir
        
        if not is_directory(input_dir):
            self._result.errors.append(f"输入目录不存在或不是目录: {input_dir}")
            return self._result
        
        self._scan_directory(input_dir)
        self._calculate_totals()
        
        return self._result
    
    def _scan_directory(self, dir_path: str) -> None:
        """递归扫描目录"""
        try:
            entries = os.listdir(dir_path)
        except PermissionError:
            self._result.errors.append(f"无权限访问目录: {dir_path}")
            return
        except Exception as e:
            self._result.errors.append(f"读取目录失败 {dir_path}: {str(e)}")
            return
        
        for entry in entries:
            full_path = os.path.join(dir_path, entry)
            
            if is_hidden_dir(full_path):
                continue
            
            if self._config.is_do_not_touch_dir(full_path):
                self._result.skipped_dirs.append(full_path)
                continue
            
            if os.path.isdir(full_path):
                self._scan_directory(full_path)
            elif os.path.isfile(full_path):
                self._process_file(full_path)
    
    def _process_file(self, file_path: str) -> None:
        """处理单个文件"""
        if is_hidden_file(file_path):
            return
        
        if not is_readable_file(file_path):
            self._result.errors.append(f"文件不可读: {file_path}")
            return
        
        filename = os.path.basename(file_path)
        extension = get_file_extension(filename)
        
        if not is_supported_file(filename, self._config.get_supported_extensions()):
            return
        
        file_type = self._config.get_file_type(extension)
        if not file_type:
            return
        
        try:
            size_bytes = os.path.getsize(file_path)
        except Exception as e:
            self._result.errors.append(f"获取文件大小失败 {file_path}: {str(e)}")
            size_bytes = 0
        
        relative_path = get_relative_path(file_path, self._config.input_dir)
        
        file_info = FileInfo(
            path=file_path,
            relative_path=relative_path,
            filename=filename,
            extension=extension,
            file_type=file_type,
            size_bytes=size_bytes
        )
        
        self._result.files.append(file_info)
    
    def _calculate_totals(self) -> None:
        """计算总计数据"""
        self._result.total_files = len(self._result.files)
        self._result.total_size = sum(f.size_bytes for f in self._result.files)
    
    def get_files_by_type(self, file_type: str) -> List[FileInfo]:
        """按文件类型获取文件列表"""
        return [f for f in self._result.files if f.file_type == file_type]


def create_scanner(config: Config) -> FileScanner:
    """创建文件扫描器实例的工厂函数"""
    return FileScanner(config)
