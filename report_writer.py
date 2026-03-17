# -*- coding: utf-8 -*-
"""
报告生成模块 - 报告生成、格式化输出
"""
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from scan_directory import FileInfo, ScanResult
from parse_content import FileParseResult
from util_config import Config, REPORT_FILENAME
from util_validators import ensure_dir_exists


@dataclass
class SummaryStats:
    """汇总统计数据"""
    total_files: int = 0
    total_size_bytes: int = 0
    files_by_type: Dict[str, int] = field(default_factory=dict)
    
    md_total_headings: int = 0
    md_total_code_blocks: int = 0
    md_total_links: int = 0
    md_total_tables: int = 0
    md_heading_by_level: Dict[int, int] = field(default_factory=dict)
    
    py_total_functions: int = 0
    py_total_classes: int = 0
    py_total_single_letter_vars: int = 0
    py_total_private_misuse: int = 0
    
    txt_total_lines: int = 0
    txt_total_words: int = 0
    
    rst_total_headings: int = 0
    rst_total_code_blocks: int = 0
    rst_total_links: int = 0
    
    html_total_headings: int = 0
    html_total_paragraphs: int = 0
    html_total_links: int = 0
    html_total_tables: int = 0


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, config: Config):
        self._config = config
        self._summary = SummaryStats()
        self._parse_results: List[FileParseResult] = []
        self._errors: List[str] = []
    
    def add_parse_result(self, result: FileParseResult) -> None:
        """添加解析结果"""
        self._parse_results.append(result)
        self._update_summary(result)
    
    def _update_summary(self, result: FileParseResult) -> None:
        """更新汇总统计"""
        self._summary.total_files += 1
        
        file_type = result.file_type
        if file_type not in self._summary.files_by_type:
            self._summary.files_by_type[file_type] = 0
        self._summary.files_by_type[file_type] += 1
        
        if result.markdown_stats:
            stats = result.markdown_stats
            for level, count in stats.heading_counts.items():
                if level not in self._summary.md_heading_by_level:
                    self._summary.md_heading_by_level[level] = 0
                self._summary.md_heading_by_level[level] += count
            self._summary.md_total_headings += sum(stats.heading_counts.values())
            self._summary.md_total_code_blocks += stats.code_block_count
            self._summary.md_total_links += stats.link_count
            self._summary.md_total_tables += stats.table_count
        
        if result.python_stats:
            stats = result.python_stats
            self._summary.py_total_functions += stats.function_count
            self._summary.py_total_classes += stats.class_count
            self._summary.py_total_single_letter_vars += stats.single_letter_var_count
            self._summary.py_total_private_misuse += len(stats.private_var_misuse)
        
        if result.text_stats:
            stats = result.text_stats
            self._summary.txt_total_lines += stats.line_count
            self._summary.txt_total_words += stats.word_count
        
        if result.rst_stats:
            stats = result.rst_stats
            self._summary.rst_total_headings += stats.heading_count
            self._summary.rst_total_code_blocks += stats.code_block_count
            self._summary.rst_total_links += stats.link_count
        
        if result.html_stats:
            stats = result.html_stats
            self._summary.html_total_headings += stats.heading_count
            self._summary.html_total_paragraphs += stats.paragraph_count
            self._summary.html_total_links += stats.link_count
            self._summary.html_total_tables += stats.table_count
    
    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self._errors.append(error)
    
    def set_scan_result(self, scan_result: ScanResult) -> None:
        """设置扫描结果"""
        self._summary.total_size_bytes = scan_result.total_size
        for error in scan_result.errors:
            self.add_error(error)
    
    def generate_report(self) -> str:
        """生成报告内容"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("多格式文档静态结构扫描与元数据提取报告")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"输入目录: {os.path.abspath(self._config.input_dir)}")
        lines.append(f"输出目录: {os.path.abspath(self._config.output_dir)}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("一、总体统计")
        lines.append("-" * 80)
        lines.append("")
        
        lines.append(f"扫描文件总数: {self._summary.total_files}")
        lines.append(f"文件总大小: {self._format_size(self._summary.total_size_bytes)}")
        lines.append("")
        
        lines.append("文件类型分布:")
        for file_type, count in sorted(self._summary.files_by_type.items()):
            lines.append(f"  - {file_type}: {count} 个文件")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("二、Markdown 文件统计")
        lines.append("-" * 80)
        lines.append("")
        
        md_count = self._summary.files_by_type.get('markdown', 0)
        lines.append(f"Markdown 文件数量: {md_count}")
        lines.append(f"标题总数: {self._summary.md_total_headings}")
        
        if self._summary.md_heading_by_level:
            lines.append("标题层级分布:")
            for level in sorted(self._summary.md_heading_by_level.keys()):
                count = self._summary.md_heading_by_level[level]
                prefix = '#' * level
                lines.append(f"  - {prefix} (H{level}): {count} 个")
        
        lines.append(f"代码块数量: {self._summary.md_total_code_blocks}")
        lines.append(f"链接数量: {self._summary.md_total_links}")
        lines.append(f"表格数量: {self._summary.md_total_tables}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("三、Python 文件统计")
        lines.append("-" * 80)
        lines.append("")
        
        py_count = self._summary.files_by_type.get('python', 0)
        lines.append(f"Python 文件数量: {py_count}")
        lines.append(f"函数定义总数: {self._summary.py_total_functions}")
        lines.append(f"类定义总数: {self._summary.py_total_classes}")
        lines.append(f"单字母变量数量: {self._summary.py_total_single_letter_vars}")
        lines.append(f"私有变量误用数量: {self._summary.py_total_private_misuse}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("四、文本文件统计")
        lines.append("-" * 80)
        lines.append("")
        
        txt_count = self._summary.files_by_type.get('text', 0)
        lines.append(f"文本文件数量: {txt_count}")
        lines.append(f"总行数: {self._summary.txt_total_lines}")
        lines.append(f"总词数: {self._summary.txt_total_words}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("五、reStructuredText 文件统计")
        lines.append("-" * 80)
        lines.append("")
        
        rst_count = self._summary.files_by_type.get('restructuredtext', 0)
        lines.append(f"RST 文件数量: {rst_count}")
        lines.append(f"标题总数: {self._summary.rst_total_headings}")
        lines.append(f"代码块数量: {self._summary.rst_total_code_blocks}")
        lines.append(f"链接数量: {self._summary.rst_total_links}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("六、HTML 文件统计")
        lines.append("-" * 80)
        lines.append("")
        
        html_count = self._summary.files_by_type.get('html', 0)
        lines.append(f"HTML 文件数量: {html_count}")
        lines.append(f"标题总数: {self._summary.html_total_headings}")
        lines.append(f"段落数量: {self._summary.html_total_paragraphs}")
        lines.append(f"链接数量: {self._summary.html_total_links}")
        lines.append(f"表格数量: {self._summary.html_total_tables}")
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("七、各文件详细统计")
        lines.append("-" * 80)
        lines.append("")
        
        for result in self._parse_results:
            lines.extend(self._format_file_result(result))
        
        if self._errors:
            lines.append("-" * 80)
            lines.append("八、错误与警告")
            lines.append("-" * 80)
            lines.append("")
            for error in self._errors:
                lines.append(f"  [!] {error}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("报告结束")
        lines.append("=" * 80)
        
        return '\n'.join(lines)
    
    def _format_file_result(self, result: FileParseResult) -> List[str]:
        """格式化单个文件的解析结果"""
        lines = []
        
        lines.append(f"文件: {result.file_path}")
        lines.append(f"类型: {result.file_type}")
        
        if result.error:
            lines.append(f"  错误: {result.error}")
            lines.append("")
            return lines
        
        if result.markdown_stats:
            stats = result.markdown_stats
            lines.append(f"  标题统计:")
            for level in sorted(stats.heading_counts.keys()):
                count = stats.heading_counts[level]
                if count > 0:
                    lines.append(f"    H{level}: {count} 个")
            lines.append(f"  代码块: {stats.code_block_count}")
            lines.append(f"  链接: {stats.link_count}")
            lines.append(f"  表格: {stats.table_count}")
        
        if result.python_stats:
            stats = result.python_stats
            lines.append(f"  函数数: {stats.function_count}")
            lines.append(f"  类数: {stats.class_count}")
            
            if stats.single_letter_vars:
                lines.append(f"  单字母变量: {', '.join(stats.single_letter_vars)}")
            
            if stats.private_var_misuse:
                lines.append(f"  私有变量误用: {', '.join(stats.private_var_misuse[:5])}")
                if len(stats.private_var_misuse) > 5:
                    lines.append(f"    ... 共 {len(stats.private_var_misuse)} 个")
        
        if result.text_stats:
            stats = result.text_stats
            lines.append(f"  行数: {stats.line_count}")
            lines.append(f"  词数: {stats.word_count}")
            lines.append(f"  字符数: {stats.char_count}")
        
        if result.rst_stats:
            stats = result.rst_stats
            lines.append(f"  标题数: {stats.heading_count}")
            lines.append(f"  代码块: {stats.code_block_count}")
            lines.append(f"  链接: {stats.link_count}")
        
        if result.html_stats:
            stats = result.html_stats
            lines.append(f"  标题数: {stats.heading_count}")
            lines.append(f"  段落数: {stats.paragraph_count}")
            lines.append(f"  链接: {stats.link_count}")
            lines.append(f"  表格: {stats.table_count}")
        
        lines.append("")
        return lines
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def save_report(self) -> Tuple[bool, Optional[str]]:
        """保存报告到文件"""
        success, error = ensure_dir_exists(self._config.output_dir)
        if not success:
            return False, error
        
        report_content = self.generate_report()
        report_path = os.path.join(self._config.output_dir, REPORT_FILENAME)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return True, None
        except Exception as e:
            return False, f"保存报告失败: {str(e)}"
    
    def get_report_path(self) -> str:
        """获取报告文件路径"""
        return os.path.join(self._config.output_dir, REPORT_FILENAME)


def create_report_generator(config: Config) -> ReportGenerator:
    """创建报告生成器实例的工厂函数"""
    return ReportGenerator(config)
