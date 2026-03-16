# -*- coding: utf-8 -*-
"""
核心解析模块 - 内容解析（md标题、py简单静态检查）
"""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from utils.config import (
    MARKDOWN_HEADING_PATTERNS,
    PYTHON_SINGLE_LETTER_VARS,
    PYTHON_DUNDER_NAMES
)


@dataclass
class MarkdownStats:
    """Markdown文件统计信息"""
    headings: Dict[int, List[str]] = field(default_factory=dict)
    heading_counts: Dict[int, int] = field(default_factory=dict)
    paragraph_count: int = 0
    code_block_count: int = 0
    link_count: int = 0
    table_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class PythonStats:
    """Python文件统计信息"""
    function_count: int = 0
    class_count: int = 0
    single_letter_vars: List[str] = field(default_factory=list)
    single_letter_var_count: int = 0
    private_var_misuse: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class TextStats:
    """文本文件统计信息"""
    line_count: int = 0
    word_count: int = 0
    char_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class RstStats:
    """reStructuredText文件统计信息"""
    heading_count: int = 0
    heading_lines: List[str] = field(default_factory=list)
    code_block_count: int = 0
    link_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class HtmlStats:
    """HTML文件统计信息"""
    heading_count: int = 0
    paragraph_count: int = 0
    link_count: int = 0
    table_count: int = 0
    code_block_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class FileParseResult:
    """文件解析结果"""
    file_path: str
    file_type: str
    markdown_stats: Optional[MarkdownStats] = None
    python_stats: Optional[PythonStats] = None
    text_stats: Optional[TextStats] = None
    rst_stats: Optional[RstStats] = None
    html_stats: Optional[HtmlStats] = None
    error: Optional[str] = None


class MarkdownParser:
    """Markdown文件解析器"""
    
    def __init__(self):
        self._heading_patterns = MARKDOWN_HEADING_PATTERNS
    
    def parse(self, content: str) -> MarkdownStats:
        """解析Markdown内容"""
        stats = MarkdownStats()
        
        try:
            lines = content.split('\n')
            
            stats = self._extract_headings(lines, stats)
            stats = self._count_code_blocks(lines, stats)
            stats = self._count_links(lines, stats)
            stats = self._count_tables(lines, stats)
            stats = self._count_paragraphs(lines, stats)
            
        except Exception as e:
            stats.errors.append(f"解析错误: {str(e)}")
        
        return stats
    
    def _extract_headings(self, lines: List[str], stats: MarkdownStats) -> MarkdownStats:
        """提取标题"""
        for level, pattern in self._heading_patterns.items():
            stats.heading_counts[level] = 0
            stats.headings[level] = []
        
        for line in lines:
            for level, pattern in self._heading_patterns.items():
                if re.match(pattern, line):
                    stats.heading_counts[level] += 1
                    heading_text = line.lstrip('#').strip()
                    stats.headings[level].append(heading_text)
                    break
        
        return stats
    
    def _count_code_blocks(self, lines: List[str], stats: MarkdownStats) -> MarkdownStats:
        """统计代码块数量"""
        code_block_pattern = r'^```'
        count = 0
        
        for line in lines:
            if re.match(code_block_pattern, line):
                count += 1
        
        stats.code_block_count = count // 2
        return stats
    
    def _count_links(self, lines: List[str], stats: MarkdownStats) -> MarkdownStats:
        """统计链接数量"""
        inline_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        ref_link_pattern = r'\[([^\]]+)\]\[([^\]]*)\]'
        
        total_links = 0
        for line in lines:
            inline_matches = len(re.findall(inline_link_pattern, line))
            ref_matches = len(re.findall(ref_link_pattern, line))
            total_links += inline_matches + ref_matches
        
        stats.link_count = total_links
        return stats
    
    def _count_tables(self, lines: List[str], stats: MarkdownStats) -> MarkdownStats:
        """统计表格数量"""
        table_row_pattern = r'^\|.*\|$'
        in_table = False
        table_count = 0
        
        for line in lines:
            if re.match(table_row_pattern, line):
                if not in_table:
                    table_count += 1
                    in_table = True
            else:
                in_table = False
        
        stats.table_count = table_count
        return stats
    
    def _count_paragraphs(self, lines: List[str], stats: MarkdownStats) -> MarkdownStats:
        """统计段落数量"""
        paragraph_count = 0
        in_paragraph = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
                if not in_paragraph:
                    paragraph_count += 1
                    in_paragraph = True
            else:
                in_paragraph = False
        
        stats.paragraph_count = paragraph_count
        return stats


class PythonParser:
    """Python文件解析器 - 使用正则表达式进行简单静态检查"""
    
    def __init__(self):
        self._single_letter_vars = set(PYTHON_SINGLE_LETTER_VARS)
        self._dunder_names = set(PYTHON_DUNDER_NAMES)
    
    def parse(self, content: str) -> PythonStats:
        """解析Python内容"""
        stats = PythonStats()
        
        try:
            lines = content.split('\n')
            
            stats = self._count_functions_and_classes(lines, stats)
            stats = self._check_single_letter_vars(content, stats)
            stats = self._check_private_var_misuse(content, stats)
            
        except Exception as e:
            stats.errors.append(f"解析错误: {str(e)}")
        
        return stats
    
    def _count_functions_and_classes(self, lines: List[str], stats: PythonStats) -> PythonStats:
        """统计函数和类定义数量"""
        func_pattern = r'^\s*def\s+\w+\s*\('
        class_pattern = r'^\s*class\s+\w+'
        
        func_count = 0
        class_count = 0
        
        for line in lines:
            if re.match(func_pattern, line):
                func_count += 1
            if re.match(class_pattern, line):
                class_count += 1
        
        stats.function_count = func_count
        stats.class_count = class_count
        return stats
    
    def _check_single_letter_vars(self, content: str, stats: PythonStats) -> PythonStats:
        """检查单字母变量"""
        assignment_pattern = r'\b([a-z])\s*='
        for_loop_pattern = r'\bfor\s+([a-z])\s+in\b'
        
        found_vars = set()
        
        matches = re.findall(assignment_pattern, content)
        for match in matches:
            if match in self._single_letter_vars:
                found_vars.add(match)
        
        matches = re.findall(for_loop_pattern, content)
        for match in matches:
            if match in self._single_letter_vars:
                found_vars.add(match)
        
        stats.single_letter_vars = list(found_vars)
        stats.single_letter_var_count = len(found_vars)
        return stats
    
    def _check_private_var_misuse(self, content: str, stats: PythonStats) -> PythonStats:
        """检查私有变量误用（下划线开头但不是__xxx__的名称）"""
        underscore_pattern = r'\b_([a-zA-Z_][a-zA-Z0-9_]*)\b'
        
        found_misuse = set()
        matches = re.findall(underscore_pattern, content)
        
        for match in matches:
            full_name = '_' + match
            if not (full_name.startswith('__') and full_name.endswith('__')):
                if full_name not in self._dunder_names:
                    found_misuse.add(full_name)
        
        stats.private_var_misuse = list(found_misuse)
        return stats


class TextParser:
    """纯文本文件解析器"""
    
    def parse(self, content: str) -> TextStats:
        """解析纯文本内容"""
        stats = TextStats()
        
        try:
            lines = content.split('\n')
            stats.line_count = len(lines)
            
            words = content.split()
            stats.word_count = len(words)
            
            stats.char_count = len(content)
            
        except Exception as e:
            stats.errors.append(f"解析错误: {str(e)}")
        
        return stats


class RstParser:
    """reStructuredText文件解析器"""
    
    def parse(self, content: str) -> RstStats:
        """解析RST内容"""
        stats = RstStats()
        
        try:
            lines = content.split('\n')
            
            stats = self._extract_headings(lines, stats)
            stats = self._count_code_blocks(lines, stats)
            stats = self._count_links(lines, stats)
            
        except Exception as e:
            stats.errors.append(f"解析错误: {str(e)}")
        
        return stats
    
    def _extract_headings(self, lines: List[str], stats: RstStats) -> RstStats:
        """提取RST标题（通过下划线识别）"""
        heading_chars = set('=-~^"\'*+')
        heading_lines = []
        
        for i in range(len(lines) - 1):
            current_line = lines[i].strip()
            next_line = lines[i + 1].strip()
            
            if current_line and next_line:
                if len(next_line) >= len(current_line):
                    if all(c in heading_chars for c in next_line):
                        heading_lines.append(current_line)
        
        stats.heading_count = len(heading_lines)
        stats.heading_lines = heading_lines
        return stats
    
    def _count_code_blocks(self, lines: List[str], stats: RstStats) -> RstStats:
        """统计代码块数量"""
        code_directive_pattern = r'^\.\.\s+(code|code-block|sourcecode)::'
        count = 0
        
        for line in lines:
            if re.match(code_directive_pattern, line):
                count += 1
        
        stats.code_block_count = count
        return stats
    
    def _count_links(self, lines: List[str], stats: RstStats) -> RstStats:
        """统计链接数量"""
        link_pattern = r'`[^`]+`_'
        count = 0
        
        for line in lines:
            matches = re.findall(link_pattern, line)
            count += len(matches)
        
        stats.link_count = count
        return stats


class HtmlParser:
    """HTML文件解析器"""
    
    def parse(self, content: str) -> HtmlStats:
        """解析HTML内容"""
        stats = HtmlStats()
        
        try:
            stats = self._count_headings(content, stats)
            stats = self._count_paragraphs(content, stats)
            stats = self._count_links(content, stats)
            stats = self._count_tables(content, stats)
            stats = self._count_code_blocks(content, stats)
            
        except Exception as e:
            stats.errors.append(f"解析错误: {str(e)}")
        
        return stats
    
    def _count_headings(self, content: str, stats: HtmlStats) -> HtmlStats:
        """统计标题数量"""
        heading_pattern = r'<h[1-6][^>]*>.*?</h[1-6]>'
        matches = re.findall(heading_pattern, content, re.IGNORECASE | re.DOTALL)
        stats.heading_count = len(matches)
        return stats
    
    def _count_paragraphs(self, content: str, stats: HtmlStats) -> HtmlStats:
        """统计段落数量"""
        p_pattern = r'<p[^>]*>.*?</p>'
        matches = re.findall(p_pattern, content, re.IGNORECASE | re.DOTALL)
        stats.paragraph_count = len(matches)
        return stats
    
    def _count_links(self, content: str, stats: HtmlStats) -> HtmlStats:
        """统计链接数量"""
        a_pattern = r'<a[^>]*href[^>]*>.*?</a>'
        matches = re.findall(a_pattern, content, re.IGNORECASE | re.DOTALL)
        stats.link_count = len(matches)
        return stats
    
    def _count_tables(self, content: str, stats: HtmlStats) -> HtmlStats:
        """统计表格数量"""
        table_pattern = r'<table[^>]*>.*?</table>'
        matches = re.findall(table_pattern, content, re.IGNORECASE | re.DOTALL)
        stats.table_count = len(matches)
        return stats
    
    def _count_code_blocks(self, content: str, stats: HtmlStats) -> HtmlStats:
        """统计代码块数量"""
        code_pattern = r'<(?:code|pre)[^>]*>.*?</(?:code|pre)>'
        matches = re.findall(code_pattern, content, re.IGNORECASE | re.DOTALL)
        stats.code_block_count = len(matches)
        return stats


class ContentParser:
    """内容解析器 - 根据文件类型选择合适的解析器"""
    
    def __init__(self):
        self._md_parser = MarkdownParser()
        self._py_parser = PythonParser()
        self._txt_parser = TextParser()
        self._rst_parser = RstParser()
        self._html_parser = HtmlParser()
    
    def parse_file(self, file_path: str, file_type: str) -> FileParseResult:
        """解析文件"""
        result = FileParseResult(file_path=file_path, file_type=file_type)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception as e:
                result.error = f"无法读取文件: {str(e)}"
                return result
        except Exception as e:
            result.error = f"读取文件失败: {str(e)}"
            return result
        
        if file_type == 'markdown':
            result.markdown_stats = self._md_parser.parse(content)
        elif file_type == 'python':
            result.python_stats = self._py_parser.parse(content)
        elif file_type == 'text':
            result.text_stats = self._txt_parser.parse(content)
        elif file_type == 'restructuredtext':
            result.rst_stats = self._rst_parser.parse(content)
        elif file_type == 'html':
            result.html_stats = self._html_parser.parse(content)
        else:
            result.error = f"不支持的文件类型: {file_type}"
        
        return result


def create_parser() -> ContentParser:
    """创建内容解析器实例的工厂函数"""
    return ContentParser()
