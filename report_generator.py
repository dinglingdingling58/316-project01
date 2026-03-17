import os
from typing import List, Dict, Any

from utils.util_config import OUTPUT_DIR, REPORT_FILE


def format_file_report(file_info: Dict[str, Any], parse_result: Dict[str, Any]) -> str:
    lines = []
    rel_path = file_info.get('relative_path', file_info.get('path', 'unknown'))
    ext = file_info.get('extension', '')

    lines.append(f"{'='*60}")
    lines.append(f"文件: {rel_path}")
    lines.append(f"类型: {ext}")
    lines.append(f"大小: {file_info.get('size', 0)} 字节")

    if 'error' in parse_result:
        lines.append(f"错误: {parse_result['error']}")
        lines.append('')
        return '\n'.join(lines)

    if ext == '.md':
        lines.append('')
        lines.append('Markdown 统计:')
        headings = parse_result.get('headings', {})
        for level in range(1, 5):
            count = headings.get(level, 0)
            lines.append(f"  {level}级标题 (#{'#'*(level-1)}): {count}个")
            if count > 0:
                for title in parse_result.get('heading_list', {}).get(level, [])[:3]:
                    lines.append(f"    - {title[:40]}...")
        lines.append(f"  代码块: {parse_result.get('code_blocks', 0)}个")
        lines.append(f"  链接: {parse_result.get('links', 0)}个")
        lines.append(f"  表格: {parse_result.get('tables', 0)}个")
        lines.append(f"  段落: {parse_result.get('paragraphs', 0)}个")

    elif ext == '.py':
        lines.append('')
        lines.append('Python 静态检查:')
        lines.append(f"  函数定义: {parse_result.get('function_count', 0)}个")
        lines.append(f"  类定义: {parse_result.get('class_count', 0)}个")
        if parse_result.get('single_letter_count', 0) > 0:
            vars_set = set(parse_result.get('single_letter_vars', []))
            lines.append(f"  单字母变量: {parse_result.get('single_letter_count', 0)}个 ({', '.join(vars_set)})")
        if parse_result.get('questionable_private_count', 0) > 0:
            priv_set = set(parse_result.get('questionable_private_vars', []))
            lines.append(f"  疑似私有变量误用: {parse_result.get('questionable_private_count', 0)}个 ({', '.join(priv_set)})")

    elif ext == '.txt':
        lines.append('')
        lines.append('文本统计:')
        lines.append(f"  总行数: {parse_result.get('total_lines', 0)}")
        lines.append(f"  非空行: {parse_result.get('non_empty_lines', 0)}")
        lines.append(f"  段落数: {parse_result.get('paragraphs', 0)}")
        lines.append(f"  单词数: {parse_result.get('word_count', 0)}")

    elif ext == '.rst':
        lines.append('')
        lines.append('RST 统计:')
        lines.append(f"  总行数: {parse_result.get('total_lines', 0)}")
        lines.append(f"  标题数: {parse_result.get('headings', 0)}")
        lines.append(f"  代码块: {parse_result.get('code_blocks', 0)}")
        lines.append(f"  链接: {parse_result.get('links', 0)}")

    elif ext == '.html':
        lines.append('')
        lines.append('HTML 统计:')
        lines.append(f"  总行数: {parse_result.get('total_lines', 0)}")
        lines.append(f"  标题数 (h1-h4): {parse_result.get('headings', 0)}")
        lines.append(f"  代码块: {parse_result.get('code_blocks', 0)}")
        lines.append(f"  链接: {parse_result.get('links', 0)}")
        lines.append(f"  表格: {parse_result.get('tables', 0)}")

    lines.append(f"  总行数: {parse_result.get('total_lines', 0)}")
    lines.append('')

    return '\n'.join(lines)


def format_summary_report(all_results: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append(f"{'#'*60}")
    lines.append(f"{'#'*20}  目录总体统计  {'#'*20}")
    lines.append(f"{'#'*60}")
    lines.append('')

    total_files = len(all_results)
    lines.append(f"总文件数: {total_files}")

    type_stats: Dict[str, int] = {}
    total_lines = 0
    total_headings = {1: 0, 2: 0, 3: 0, 4: 0}
    total_functions = 0
    total_classes = 0
    total_code_blocks = 0
    total_links = 0
    total_tables = 0

    for result in all_results:
        ext = result.get('file_info', {}).get('extension', '')
        type_stats[ext] = type_stats.get(ext, 0) + 1

        parse_res = result.get('parse_result', {})
        total_lines += parse_res.get('total_lines', 0)

        if ext == '.md':
            headings = parse_res.get('headings', {})
            for lvl in range(1, 5):
                total_headings[lvl] += headings.get(lvl, 0)
            total_code_blocks += parse_res.get('code_blocks', 0)
            total_links += parse_res.get('links', 0)
            total_tables += parse_res.get('tables', 0)
        elif ext == '.py':
            total_functions += parse_res.get('function_count', 0)
            total_classes += parse_res.get('class_count', 0)

    lines.append('')
    lines.append('文件类型分布:')
    for ext, count in sorted(type_stats.items()):
        lines.append(f"  {ext}: {count}个")

    lines.append('')
    lines.append(f"总行数: {total_lines}")
    lines.append('')
    lines.append('Markdown 汇总:')
    for lvl in range(1, 5):
        lines.append(f"  {lvl}级标题总数: {total_headings[lvl]}")
    lines.append(f"  代码块总数: {total_code_blocks}")
    lines.append(f"  链接总数: {total_links}")
    lines.append(f"  表格总数: {total_tables}")

    lines.append('')
    lines.append('Python 汇总:')
    lines.append(f"  函数总数: {total_functions}")
    lines.append(f"  类总数: {total_classes}")

    return '\n'.join(lines)


def generate_report(all_results: List[Dict[str, Any]], output_dir: str) -> str:
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass

    report_lines = []
    report_lines.append('=' * 60)
    report_lines.append('多格式文档静态结构扫描与元数据提取工具')
    report_lines.append('分析报告')
    report_lines.append('=' * 60)
    report_lines.append('')

    report_lines.append(format_summary_report(all_results))
    report_lines.append('')
    report_lines.append('')

    report_lines.append('=' * 60)
    report_lines.append('单文件详细统计')
    report_lines.append('=' * 60)
    report_lines.append('')

    for result in all_results:
        file_report = format_file_report(result.get('file_info', {}), result.get('parse_result', {}))
        report_lines.append(file_report)

    full_report = '\n'.join(report_lines)

    report_path = os.path.join(output_dir, REPORT_FILE)
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
    except Exception:
        pass

    return full_report
