"""
核心解析模块 - 负责内容解析（Markdown标题、Python简单静态检查）。

技术约束：
- 只使用字符串操作 + 正则表达式
- 不使用 ast 模块
- 不使用第三方包
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field

from utils.config import (
    MARKDOWN_HEADER_PATTERN,
    MARKDOWN_CODE_BLOCK_PATTERN,
    MARKDOWN_INLINE_CODE_PATTERN,
    MARKDOWN_LINK_PATTERN,
    MARKDOWN_TABLE_PATTERN,
    PYTHON_SINGLE_LETTER_VARS,
    PYTHON_FUNCTION_PATTERN,
    PYTHON_CLASS_PATTERN,
    PYTHON_VARIABLE_ASSIGNMENT_PATTERN,
    HTML_TITLE_PATTERN,
    HTML_HEADER_PATTERNS,
    HTML_LINK_PATTERN,
    HTML_TABLE_PATTERN,
)


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class MarkdownStats:
    """Markdown 文件统计信息。"""
    
    # 标题统计
    header_counts: Dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0})
    headers: List[Tuple[int, str]] = field(default_factory=list)  # (级别, 标题文本)
    
    # 内容统计
    paragraph_count: int = 0
    code_block_count: int = 0
    inline_code_count: int = 0
    link_count: int = 0
    table_count: int = 0
    
    # 错误信息
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'header_counts': self.header_counts.copy(),
            'headers': self.headers.copy(),
            'paragraph_count': self.paragraph_count,
            'code_block_count': self.code_block_count,
            'inline_code_count': self.inline_code_count,
            'link_count': self.link_count,
            'table_count': self.table_count,
            'total_headers': sum(self.header_counts.values()),
            'error_message': self.error_message,
        }


@dataclass
class PythonStats:
    """Python 文件统计信息。"""
    
    # 定义统计
    function_count: int = 0
    class_count: int = 0
    function_names: List[str] = field(default_factory=list)
    class_names: List[str] = field(default_factory=list)
    
    # 命名规范问题
    single_letter_variables: List[str] = field(default_factory=list)
    improper_private_names: List[str] = field(default_factory=list)
    
    # 代码统计
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # 错误信息
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'function_count': self.function_count,
            'class_count': self.class_count,
            'function_names': self.function_names.copy(),
            'class_names': self.class_names.copy(),
            'single_letter_variables': self.single_letter_variables.copy(),
            'improper_private_names': self.improper_private_names.copy(),
            'total_lines': self.total_lines,
            'code_lines': self.code_lines,
            'comment_lines': self.comment_lines,
            'blank_lines': self.blank_lines,
            'error_message': self.error_message,
        }


@dataclass
class TextStats:
    """纯文本文件统计信息。"""
    
    total_lines: int = 0
    total_chars: int = 0
    non_empty_lines: int = 0
    word_count: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'total_lines': self.total_lines,
            'total_chars': self.total_chars,
            'non_empty_lines': self.non_empty_lines,
            'word_count': self.word_count,
            'error_message': self.error_message,
        }


@dataclass
class HtmlStats:
    """HTML 文件统计信息。"""
    
    title: Optional[str] = None
    header_counts: Dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0})
    headers: List[Tuple[int, str]] = field(default_factory=list)
    link_count: int = 0
    table_count: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'title': self.title,
            'header_counts': self.header_counts.copy(),
            'headers': self.headers.copy(),
            'link_count': self.link_count,
            'table_count': self.table_count,
            'total_headers': sum(self.header_counts.values()),
            'error_message': self.error_message,
        }


@dataclass
class RstStats:
    """reStructuredText 文件统计信息。"""
    
    header_counts: Dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0})
    headers: List[Tuple[int, str]] = field(default_factory=list)
    directive_count: int = 0
    link_count: int = 0
    table_count: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'header_counts': self.header_counts.copy(),
            'headers': self.headers.copy(),
            'directive_count': self.directive_count,
            'link_count': self.link_count,
            'table_count': self.table_count,
            'total_headers': sum(self.header_counts.values()),
            'error_message': self.error_message,
        }


# =============================================================================
# Markdown 解析器
# =============================================================================

class MarkdownParser:
    """Markdown 文件解析器。"""
    
    @staticmethod
    def parse(content: str) -> MarkdownStats:
        """
        解析 Markdown 内容。
        
        Args:
            content: 文件内容
            
        Returns:
            MarkdownStats 对象
        """
        stats = MarkdownStats()
        
        try:
            lines = content.split('\n')
            
            # 解析标题
            for line in lines:
                match = re.match(MARKDOWN_HEADER_PATTERN, line.strip())
                if match:
                    level = len(match.group(1))
                    title = match.group(2).strip()
                    stats.header_counts[level] = stats.header_counts.get(level, 0) + 1
                    stats.headers.append((level, title))
            
            # 统计段落（非空行且不是标题、代码块标记等）
            in_code_block = False
            for line in lines:
                stripped = line.strip()
                
                # 检测代码块开始/结束
                if stripped.startswith('```'):
                    in_code_block = not in_code_block
                    if not in_code_block:
                        stats.code_block_count += 1
                    continue
                
                # 统计段落
                if not in_code_block and stripped and not stripped.startswith('#'):
                    # 简单的段落检测：非空行且不是列表项等
                    if not re.match(r'^[-*+\d]\s', stripped):
                        stats.paragraph_count += 1
            
            # 统计行内代码
            stats.inline_code_count = len(re.findall(MARKDOWN_INLINE_CODE_PATTERN, content))
            
            # 统计链接
            stats.link_count = len(re.findall(MARKDOWN_LINK_PATTERN, content))
            
            # 统计表格（简化检测）
            stats.table_count = len(re.findall(MARKDOWN_TABLE_PATTERN, content))
            
        except Exception as e:
            stats.error_message = f"解析 Markdown 时出错: {str(e)}"
        
        return stats


# =============================================================================
# Python 解析器
# =============================================================================

class PythonParser:
    """Python 文件解析器（简单静态检查，不使用 AST）。"""
    
    @staticmethod
    def parse(content: str) -> PythonStats:
        """
        解析 Python 内容。
        
        Args:
            content: 文件内容
            
        Returns:
            PythonStats 对象
        """
        stats = PythonStats()
        
        try:
            lines = content.split('\n')
            stats.total_lines = len(lines)
            
            all_variables: Set[str] = set()
            
            for line in lines:
                stripped = line.strip()
                
                # 空行
                if not stripped:
                    stats.blank_lines += 1
                    continue
                
                # 注释行
                if stripped.startswith('#'):
                    stats.comment_lines += 1
                    continue
                
                # 代码行
                stats.code_lines += 1
                
                # 检测函数定义
                func_match = re.match(PYTHON_FUNCTION_PATTERN, line)
                if func_match:
                    func_name = func_match.group(1)
                    stats.function_count += 1
                    stats.function_names.append(func_name)
                    continue
                
                # 检测类定义
                class_match = re.match(PYTHON_CLASS_PATTERN, line)
                if class_match:
                    class_name = class_match.group(1)
                    stats.class_count += 1
                    stats.class_names.append(class_name)
                    continue
                
                # 收集变量赋值
                var_matches = re.findall(PYTHON_VARIABLE_ASSIGNMENT_PATTERN, line)
                for var_name in var_matches:
                    all_variables.add(var_name)
            
            # 检查单字母变量
            for var in all_variables:
                if var in PYTHON_SINGLE_LETTER_VARS:
                    stats.single_letter_variables.append(var)
            
            # 检查不规范的私有变量命名
            # 下划线开头但不是 __xxx__ 的名称
            for var in all_variables:
                if var.startswith('_') and not (var.startswith('__') and var.endswith('__')):
                    # 排除单下划线（常用于忽略变量）
                    if var != '_':
                        stats.improper_private_names.append(var)
            
            # 去重
            stats.single_letter_variables = list(set(stats.single_letter_variables))
            stats.improper_private_names = list(set(stats.improper_private_names))
            
        except Exception as e:
            stats.error_message = f"解析 Python 时出错: {str(e)}"
        
        return stats


# =============================================================================
# 纯文本解析器
# =============================================================================

class TextParser:
    """纯文本文件解析器。"""
    
    @staticmethod
    def parse(content: str) -> TextStats:
        """
        解析纯文本内容。
        
        Args:
            content: 文件内容
            
        Returns:
            TextStats 对象
        """
        stats = TextStats()
        
        try:
            lines = content.split('\n')
            stats.total_lines = len(lines)
            stats.total_chars = len(content)
            
            for line in lines:
                stripped = line.strip()
                if stripped:
                    stats.non_empty_lines += 1
                    # 简单的单词统计
                    words = re.findall(r'\b\w+\b', stripped)
                    stats.word_count += len(words)
            
        except Exception as e:
            stats.error_message = f"解析文本时出错: {str(e)}"
        
        return stats


# =============================================================================
# HTML 解析器
# =============================================================================

class HtmlParser:
    """HTML 文件解析器。"""
    
    @staticmethod
    def parse(content: str) -> HtmlStats:
        """
        解析 HTML 内容。
        
        Args:
            content: 文件内容
            
        Returns:
            HtmlStats 对象
        """
        stats = HtmlStats()
        
        try:
            # 提取标题
            title_match = re.search(HTML_TITLE_PATTERN, content, re.IGNORECASE)
            if title_match:
                stats.title = title_match.group(1).strip()
            
            # 提取各级标题
            for level, pattern in enumerate(HTML_HEADER_PATTERNS, start=1):
                matches = re.findall(pattern, content, re.IGNORECASE)
                stats.header_counts[level] = len(matches)
                for match in matches:
                    # 清理 HTML 标签
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text:
                        stats.headers.append((level, clean_text))
            
            # 统计链接
            stats.link_count = len(re.findall(HTML_LINK_PATTERN, content, re.IGNORECASE))
            
            # 统计表格
            stats.table_count = len(re.findall(HTML_TABLE_PATTERN, content, re.IGNORECASE))
            
        except Exception as e:
            stats.error_message = f"解析 HTML 时出错: {str(e)}"
        
        return stats


# =============================================================================
# reStructuredText 解析器
# =============================================================================

class RstParser:
    """reStructuredText 文件解析器。"""
    
    @staticmethod
    def parse(content: str) -> RstStats:
        """
        解析 reStructuredText 内容。
        
        Args:
            content: 文件内容
            
        Returns:
            RstStats 对象
        """
        stats = RstStats()
        
        try:
            lines = content.split('\n')
            
            # RST 标题是通过下划线/上划线标记的
            # 我们需要检测这种模式
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # 检测标题（当前行是文字，下一行是标点符号）
                if i + 1 < len(lines) and stripped:
                    next_line = lines[i + 1].strip()
                    # 检查下一行是否全是相同的标点符号
                    if next_line and len(set(next_line)) == 1 and next_line[0] in '=-~^"\'`':
                        # 这是一个标题
                        level_char = next_line[0]
                        level_map = {'=': 1, '-': 2, '~': 3, '^': 4}
                        level = level_map.get(level_char, 1)
                        
                        stats.header_counts[level] = stats.header_counts.get(level, 0) + 1
                        stats.headers.append((level, stripped))
                        i += 2  # 跳过标题行和标记行
                        continue
                
                i += 1
            
            # 统计指令
            stats.directive_count = len(re.findall(r'^\s*\.\.\s+\w+::', content, re.MULTILINE))
            
            # 统计链接
            stats.link_count = len(re.findall(r'`[^<]+<[^>]+>`_', content))
            
            # 统计表格（简化检测）
            stats.table_count = len(re.findall(r'\+[-+]+\+', content))
            
        except Exception as e:
            stats.error_message = f"解析 reStructuredText 时出错: {str(e)}"
        
        return stats


# =============================================================================
# 通用解析接口
# =============================================================================

class ContentParser:
    """通用内容解析器 - 根据文件类型自动选择解析器。"""
    
    PARSERS = {
        '.md': MarkdownParser,
        '.py': PythonParser,
        '.txt': TextParser,
        '.rst': RstParser,
        '.html': HtmlParser,
    }
    
    @classmethod
    def parse_file(cls, filepath: str, extension: str) -> Dict[str, Any]:
        """
        解析文件内容。
        
        Args:
            filepath: 文件路径
            extension: 文件扩展名
            
        Returns:
            解析结果字典
        """
        result: Dict[str, Any] = {
            'filepath': filepath,
            'extension': extension,
            'success': False,
            'data': None,
            'error': None,
        }
        
        try:
            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 选择解析器
            parser_class = cls.PARSERS.get(extension.lower())
            if parser_class:
                stats = parser_class.parse(content)
                result['success'] = True
                result['data'] = stats.to_dict()
            else:
                result['error'] = f"不支持的文件类型: {extension}"
                
        except Exception as e:
            result['error'] = f"读取或解析文件时出错: {str(e)}"
        
        return result
