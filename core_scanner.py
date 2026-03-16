"""
核心扫描模块 - 负责文件系统遍历、类型识别、文件过滤。

路径约束：
- 输入目录： ./source_data/
- 输出目录： ./output_build/
- 禁止在 ./source_data/ 目录下创建、修改、删除、重命名任何文件
"""

import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from utils.config import (
    INPUT_DIRECTORY,
    SUPPORTED_EXTENSIONS,
    read_protected_marker,
)
from utils.validators import (
    validate_source_filename,
    is_binary_file,
    is_protected_path,
    get_relative_path,
)


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class FileInfo:
    """文件信息数据类。"""
    
    absolute_path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    is_binary: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'absolute_path': self.absolute_path,
            'relative_path': self.relative_path,
            'filename': self.filename,
            'extension': self.extension,
            'size_bytes': self.size_bytes,
            'is_binary': self.is_binary,
            'error_message': self.error_message,
        }


@dataclass
class ScanResult:
    """扫描结果数据类。"""
    
    total_files_found: int = 0
    files_scanned: int = 0
    files_skipped: int = 0
    files_with_errors: int = 0
    file_list: List[FileInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    protected_paths: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'total_files_found': self.total_files_found,
            'files_scanned': self.files_scanned,
            'files_skipped': self.files_skipped,
            'files_with_errors': self.files_with_errors,
            'file_list': [f.to_dict() for f in self.file_list],
            'errors': self.errors,
            'protected_paths': self.protected_paths,
        }


# =============================================================================
# 文件扫描器
# =============================================================================

class FileScanner:
    """
    文件扫描器类 - 递归扫描目录并识别支持的文件类型。
    
    重要约束：
    - 只处理指定扩展名的文件
    - 禁止修改 source_data 目录下的任何内容
    """
    
    def __init__(
        self,
        input_dir: str = INPUT_DIRECTORY,
        extensions: Optional[List[str]] = None,
    ):
        """
        初始化文件扫描器。
        
        Args:
            input_dir: 输入目录路径
            extensions: 要处理的文件扩展名列表（默认为 SUPPORTED_EXTENSIONS）
        """
        self.input_dir = os.path.abspath(input_dir)
        self.extensions = set(extensions) if extensions else SUPPORTED_EXTENSIONS
        self.config = read_protected_marker()
        self.protected_paths = self.config.get('protected_paths', [])
        self._should_stop = False
    
    def _is_supported_extension(self, filename: str) -> bool:
        """
        检查文件扩展名是否受支持。
        
        Args:
            filename: 文件名
            
        Returns:
            如果扩展名受支持返回 True
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.extensions
    
    def _should_process_file(self, filepath: str) -> bool:
        """
        检查是否应该处理该文件。
        
        Args:
            filepath: 文件完整路径
            
        Returns:
            如果应该处理返回 True
        """
        # 检查是否是受保护的路径
        if is_protected_path(filepath, self.protected_paths, self.input_dir):
            return False
        
        # 检查文件扩展名
        filename = os.path.basename(filepath)
        if not self._is_supported_extension(filename):
            return False
        
        # 验证文件名
        is_valid, _ = validate_source_filename(filename)
        if not is_valid:
            return False
        
        return True
    
    def _collect_file_info(self, filepath: str) -> FileInfo:
        """
        收集文件信息。
        
        Args:
            filepath: 文件完整路径
            
        Returns:
            FileInfo 对象
        """
        filename = os.path.basename(filepath)
        extension = os.path.splitext(filename)[1].lower()
        relative_path = get_relative_path(filepath, self.input_dir)
        
        try:
            size_bytes = os.path.getsize(filepath)
        except OSError:
            size_bytes = 0
        
        # 检测是否为二进制文件
        is_binary = is_binary_file(filepath)
        
        return FileInfo(
            absolute_path=filepath,
            relative_path=relative_path,
            filename=filename,
            extension=extension,
            size_bytes=size_bytes,
            is_binary=is_binary,
        )
    
    def scan(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ScanResult:
        """
        递归扫描输入目录。
        
        Args:
            progress_callback: 进度回调函数，接收当前处理的文件路径
            
        Returns:
            ScanResult 对象
        """
        result = ScanResult()
        result.protected_paths = self.protected_paths.copy()
        
        # 检查输入目录是否存在
        if not os.path.exists(self.input_dir):
            result.errors.append(f"输入目录不存在: {self.input_dir}")
            return result
        
        if not os.path.isdir(self.input_dir):
            result.errors.append(f"输入路径不是目录: {self.input_dir}")
            return result
        
        # 递归遍历目录
        for root, dirs, files in os.walk(self.input_dir):
            if self._should_stop:
                break
            
            # 过滤掉受保护的子目录
            dirs[:] = [
                d for d in dirs
                if not is_protected_path(
                    os.path.join(root, d),
                    self.protected_paths,
                    self.input_dir,
                )
            ]
            
            for filename in files:
                if self._should_stop:
                    break
                
                filepath = os.path.join(root, filename)
                result.total_files_found += 1
                
                # 报告进度
                if progress_callback:
                    progress_callback(filepath)
                
                # 检查是否应该处理
                if not self._should_process_file(filepath):
                    result.files_skipped += 1
                    continue
                
                # 收集文件信息
                try:
                    file_info = self._collect_file_info(filepath)
                    
                    if file_info.is_binary:
                        file_info.error_message = "二进制文件，跳过内容解析"
                        result.files_with_errors += 1
                    
                    result.file_list.append(file_info)
                    result.files_scanned += 1
                    
                except Exception as e:
                    result.errors.append(f"处理文件时出错 {filepath}: {str(e)}")
                    result.files_with_errors += 1
        
        return result
    
    def stop(self) -> None:
        """停止扫描过程。"""
        self._should_stop = True
    
    def get_statistics(self, result: ScanResult) -> Dict[str, Any]:
        """
        获取扫描统计信息。
        
        Args:
            result: 扫描结果
            
        Returns:
            统计信息字典
        """
        extension_counts: Dict[str, int] = {}
        for file_info in result.file_list:
            ext = file_info.extension
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        total_size = sum(f.size_bytes for f in result.file_list)
        
        return {
            'total_files_found': result.total_files_found,
            'files_scanned': result.files_scanned,
            'files_skipped': result.files_skipped,
            'files_with_errors': result.files_with_errors,
            'extension_distribution': extension_counts,
            'total_size_bytes': total_size,
        }


def scan_directory(
    input_dir: str = INPUT_DIRECTORY,
    extensions: Optional[List[str]] = None,
) -> ScanResult:
    """
    便捷函数：扫描目录。
    
    Args:
        input_dir: 输入目录
        extensions: 文件扩展名列表
        
    Returns:
        ScanResult 对象
    """
    scanner = FileScanner(input_dir, extensions)
    return scanner.scan()
