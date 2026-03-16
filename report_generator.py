"""
报告生成模块 - 负责报告生成、格式化输出。

输出要求：
- 生成一份汇总报告（纯文本），保存为 analysis-report.txt
- 报告中需包含每个文件的简要统计 + 全目录总体统计
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from utils.config import (
    OUTPUT_DIRECTORY,
    REPORT_FILENAME,
    get_output_report_path,
    ensure_output_directory,
    INPUT_DIRECTORY,
)
from utils.validators import format_count


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class FileReport:
    """单个文件的报告数据。"""
    
    filepath: str
    extension: str
    size_bytes: int
    parse_result: Dict[str, Any] = field(default_factory=dict)
    
    def to_text(self, indent: int = 2) -> str:
        """转换为文本格式。"""
        indent_str = ' ' * indent
        lines = []
        
        lines.append(f"{indent_str}文件: {self.filepath}")
        lines.append(f"{indent_str}  类型: {self.extension}")
        lines.append(f"{indent_str}  大小: {self._format_size()}")
        
        if self.parse_result.get('success'):
            data = self.parse_result.get('data', {})
            lines.extend(self._format_stats(data, indent + 2))
        else:
            error = self.parse_result.get('error', '未知错误')
            lines.append(f"{indent_str}  错误: {error}")
        
        return '\n'.join(lines)
    
    def _format_size(self) -> str:
        """格式化文件大小。"""
        size = self.size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"
    
    def _format_stats(self, data: Dict[str, Any], indent: int) -> List[str]:
        """格式化统计信息。"""
        indent_str = ' ' * indent
        lines = []
        
        ext = self.extension.lower()
        
        if ext == '.md':
            # Markdown 统计
            header_counts = data.get('header_counts', {})
            total_headers = data.get('total_headers', 0)
            lines.append(f"{indent_str}标题统计:")
            for level in range(1, 5):
                count = header_counts.get(level, 0)
                lines.append(f"{indent_str}  H{level}: {count} 个")
            lines.append(f"{indent_str}  总计: {total_headers} 个标题")
            lines.append(f"{indent_str}段落数: {data.get('paragraph_count', 0)}")
            lines.append(f"{indent_str}代码块: {data.get('code_block_count', 0)}")
            lines.append(f"{indent_str}行内代码: {data.get('inline_code_count', 0)}")
            lines.append(f"{indent_str}链接数: {data.get('link_count', 0)}")
            lines.append(f"{indent_str}表格数: {data.get('table_count', 0)}")
            
        elif ext == '.py':
            # Python 统计
            lines.append(f"{indent_str}代码统计:")
            lines.append(f"{indent_str}  总行数: {data.get('total_lines', 0)}")
            lines.append(f"{indent_str}  代码行: {data.get('code_lines', 0)}")
            lines.append(f"{indent_str}  注释行: {data.get('comment_lines', 0)}")
            lines.append(f"{indent_str}  空行: {data.get('blank_lines', 0)}")
            lines.append(f"{indent_str}定义统计:")
            lines.append(f"{indent_str}  函数: {data.get('function_count', 0)}")
            lines.append(f"{indent_str}  类: {data.get('class_count', 0)}")
            
            # 命名规范问题
            single_vars = data.get('single_letter_variables', [])
            if single_vars:
                lines.append(f"{indent_str}命名警告:")
                lines.append(f"{indent_str}  单字母变量: {', '.join(single_vars[:10])}")
                if len(single_vars) > 10:
                    lines.append(f"{indent_str}    ... 等共 {len(single_vars)} 个")
            
            improper_private = data.get('improper_private_names', [])
            if improper_private:
                lines.append(f"{indent_str}  不规范私有变量: {', '.join(improper_private[:10])}")
                if len(improper_private) > 10:
                    lines.append(f"{indent_str}    ... 等共 {len(improper_private)} 个")
                    
        elif ext == '.txt':
            # 文本统计
            lines.append(f"{indent_str}文本统计:")
            lines.append(f"{indent_str}  总行数: {data.get('total_lines', 0)}")
            lines.append(f"{indent_str}  非空行: {data.get('non_empty_lines', 0)}")
            lines.append(f"{indent_str}  字符数: {data.get('total_chars', 0)}")
            lines.append(f"{indent_str}  单词数: {data.get('word_count', 0)}")
            
        elif ext == '.html':
            # HTML 统计
            title = data.get('title')
            if title:
                lines.append(f"{indent_str}页面标题: {title}")
            
            header_counts = data.get('header_counts', {})
            total_headers = data.get('total_headers', 0)
            lines.append(f"{indent_str}标题统计:")
            for level in range(1, 5):
                count = header_counts.get(level, 0)
                lines.append(f"{indent_str}  H{level}: {count} 个")
            lines.append(f"{indent_str}  总计: {total_headers} 个标题")
            lines.append(f"{indent_str}链接数: {data.get('link_count', 0)}")
            lines.append(f"{indent_str}表格数: {data.get('table_count', 0)}")
            
        elif ext == '.rst':
            # RST 统计
            header_counts = data.get('header_counts', {})
            total_headers = data.get('total_headers', 0)
            lines.append(f"{indent_str}标题统计:")
            for level in range(1, 5):
                count = header_counts.get(level, 0)
                lines.append(f"{indent_str}  级别 {level}: {count} 个")
            lines.append(f"{indent_str}  总计: {total_headers} 个标题")
            lines.append(f"{indent_str}指令数: {data.get('directive_count', 0)}")
            lines.append(f"{indent_str}链接数: {data.get('link_count', 0)}")
            lines.append(f"{indent_str}表格数: {data.get('table_count', 0)}")
        
        return lines


@dataclass
class SummaryReport:
    """汇总报告数据。"""
    
    scan_stats: Dict[str, Any] = field(default_factory=dict)
    file_reports: List[FileReport] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_text(self) -> str:
        """转换为完整的文本报告。"""
        lines = []
        
        # 报告头
        lines.append("=" * 80)
        lines.append("文档静态结构扫描与元数据提取报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"输入目录: {os.path.abspath(INPUT_DIRECTORY)}")
        lines.append(f"输出目录: {os.path.abspath(OUTPUT_DIRECTORY)}")
        lines.append("")
        
        # 扫描统计摘要
        lines.append("-" * 80)
        lines.append("一、扫描统计摘要")
        lines.append("-" * 80)
        lines.append("")
        lines.append(self._format_scan_summary())
        lines.append("")
        
        # 文件类型分布
        lines.append("-" * 80)
        lines.append("二、文件类型分布")
        lines.append("-" * 80)
        lines.append("")
        lines.append(self._format_extension_distribution())
        lines.append("")
        
        # 各文件详细统计
        lines.append("-" * 80)
        lines.append("三、各文件详细统计")
        lines.append("-" * 80)
        lines.append("")
        
        for i, file_report in enumerate(self.file_reports, 1):
            lines.append(f"[{i}/{len(self.file_reports)}]")
            lines.append(file_report.to_text())
            lines.append("")
        
        # 错误记录
        if self.errors:
            lines.append("-" * 80)
            lines.append("四、错误记录")
            lines.append("-" * 80)
            lines.append("")
            for error in self.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        # 报告尾
        lines.append("=" * 80)
        lines.append("报告生成完毕")
        lines.append("=" * 80)
        
        return '\n'.join(lines)
    
    def _format_scan_summary(self) -> str:
        """格式化扫描摘要。"""
        lines = []
        
        total_found = self.scan_stats.get('total_files_found', 0)
        scanned = self.scan_stats.get('files_scanned', 0)
        skipped = self.scan_stats.get('files_skipped', 0)
        errors = self.scan_stats.get('files_with_errors', 0)
        total_size = self.scan_stats.get('total_size_bytes', 0)
        
        lines.append(f"  发现文件总数: {total_found}")
        lines.append(f"  已扫描文件: {scanned}")
        lines.append(f"  跳过文件: {skipped}")
        lines.append(f"  错误文件: {errors}")
        lines.append(f"  扫描文件总大小: {self._format_bytes(total_size)}")
        
        return '\n'.join(lines)
    
    def _format_extension_distribution(self) -> str:
        """格式化文件类型分布。"""
        lines = []
        
        ext_dist = self.scan_stats.get('extension_distribution', {})
        if not ext_dist:
            lines.append("  无文件类型分布数据")
        else:
            # 按数量排序
            sorted_exts = sorted(ext_dist.items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_exts:
                lines.append(f"  {ext}: {count} 个文件")
        
        return '\n'.join(lines)
    
    def _format_bytes(self, size: int) -> str:
        """格式化字节大小。"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


# =============================================================================
# 报告生成器
# =============================================================================

class ReportGenerator:
    """报告生成器类。"""
    
    def __init__(self, output_dir: str = OUTPUT_DIRECTORY):
        """
        初始化报告生成器。
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.report_path = get_output_report_path()
    
    def generate(
        self,
        scan_stats: Dict[str, Any],
        parse_results: List[Dict[str, Any]],
        errors: List[str],
    ) -> str:
        """
        生成报告。
        
        Args:
            scan_stats: 扫描统计信息
            parse_results: 解析结果列表
            errors: 错误列表
            
        Returns:
            生成的报告内容
        """
        # 确保输出目录存在
        ensure_output_directory()
        
        # 构建文件报告列表
        file_reports = []
        for result in parse_results:
            file_report = FileReport(
                filepath=result.get('filepath', ''),
                extension=result.get('extension', ''),
                size_bytes=result.get('size_bytes', 0),
                parse_result={
                    'success': result.get('success', False),
                    'data': result.get('data', {}),
                    'error': result.get('error', None),
                },
            )
            file_reports.append(file_report)
        
        # 构建汇总报告
        summary = SummaryReport(
            scan_stats=scan_stats,
            file_reports=file_reports,
            errors=errors,
        )
        
        # 生成报告文本
        report_content = summary.to_text()
        
        return report_content
    
    def save(self, content: str) -> bool:
        """
        保存报告到文件。
        
        Args:
            content: 报告内容
            
        Returns:
            保存成功返回 True
        """
        try:
            with open(self.report_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def generate_and_save(
        self,
        scan_stats: Dict[str, Any],
        parse_results: List[Dict[str, Any]],
        errors: List[str],
    ) -> Tuple[bool, str]:
        """
        生成并保存报告。
        
        Args:
            scan_stats: 扫描统计信息
            parse_results: 解析结果列表
            errors: 错误列表
            
        Returns:
            (是否成功, 报告内容或错误信息)
        """
        try:
            content = self.generate(scan_stats, parse_results, errors)
            if self.save(content):
                return True, content
            else:
                return False, "保存报告文件失败"
        except Exception as e:
            return False, f"生成报告时出错: {str(e)}"


# =============================================================================
# 便捷函数
# =============================================================================

def generate_report(
    scan_stats: Dict[str, Any],
    parse_results: List[Dict[str, Any]],
    errors: List[str],
    output_dir: str = OUTPUT_DIRECTORY,
) -> Tuple[bool, str]:
    """
    便捷函数：生成并保存报告。
    
    Args:
        scan_stats: 扫描统计信息
        parse_results: 解析结果列表
        errors: 错误列表
        output_dir: 输出目录
        
    Returns:
        (是否成功, 报告内容或错误信息)
    """
    generator = ReportGenerator(output_dir)
    return generator.generate_and_save(scan_stats, parse_results, errors)
