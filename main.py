# -*- coding: utf-8 -*-
"""
多格式文档静态结构扫描与元数据提取工具
主入口模块 - 负责参数解析与流程调度
"""
import sys
from typing import Optional, List

from utils.config import create_config, Config
from utils.validators import is_directory, ensure_dir_exists
from core_scanner import create_scanner, FileScanner, ScanResult
from core_parser import create_parser, ContentParser, FileParseResult
from report_generator import create_report_generator, ReportGenerator


def print_banner() -> None:
    """打印程序横幅"""
    banner = """
================================================================================
    多格式文档静态结构扫描与元数据提取工具
    Document Static Structure Scanner & Metadata Extractor
================================================================================
"""
    print(banner)


def print_info(message: str) -> None:
    """打印信息"""
    print(f"[INFO] {message}")


def print_warning(message: str) -> None:
    """打印警告"""
    print(f"[WARN] {message}")


def print_error(message: str) -> None:
    """打印错误"""
    print(f"[ERROR] {message}", file=sys.stderr)


def validate_environment(config: Config) -> bool:
    """验证运行环境"""
    input_dir = config.input_dir
    output_dir = config.output_dir
    
    if not is_directory(input_dir):
        print_error(f"输入目录不存在: {input_dir}")
        print_info(f"请创建输入目录并添加文档文件")
        return False
    
    success, error = ensure_dir_exists(output_dir)
    if not success:
        print_error(f"无法创建输出目录: {error}")
        return False
    
    return True


def run_scanner(scanner: FileScanner) -> ScanResult:
    """运行文件扫描"""
    print_info("开始扫描文件...")
    result = scanner.scan()
    print_info(f"扫描完成，共发现 {result.total_files} 个支持的文件")
    
    if result.errors:
        for error in result.errors:
            print_warning(error)
    
    return result


def run_parser(parser: ContentParser, scan_result: ScanResult, reporter: ReportGenerator) -> None:
    """运行内容解析"""
    print_info("开始解析文件内容...")
    
    total = len(scan_result.files)
    for idx, file_info in enumerate(scan_result.files, 1):
        print(f"\r  处理进度: [{idx}/{total}] {file_info.filename}", end="", flush=True)
        
        result = parser.parse_file(file_info.path, file_info.file_type)
        
        if result.error:
            reporter.add_error(f"{file_info.relative_path}: {result.error}")
        
        reporter.add_parse_result(result)
    
    print()
    print_info("文件解析完成")


def run_reporter(reporter: ReportGenerator) -> Optional[str]:
    """生成并保存报告"""
    print_info("生成分析报告...")
    
    success, error = reporter.save_report()
    
    if success:
        report_path = reporter.get_report_path()
        print_info(f"报告已保存: {report_path}")
        return report_path
    else:
        print_error(f"保存报告失败: {error}")
        return None


def main(args: Optional[List[str]] = None) -> int:
    """主函数"""
    print_banner()
    
    config = create_config()
    
    if not validate_environment(config):
        return 1
    
    if not config.load_do_not_touch_config():
        for error in config.errors:
            print_warning(error)
    
    scanner = create_scanner(config)
    scan_result = run_scanner(scanner)
    
    if scan_result.total_files == 0:
        print_warning("未发现任何支持的文件")
        print_info(f"支持的文件类型: {', '.join(config.get_supported_extensions())}")
        return 0
    
    parser = create_parser()
    reporter = create_report_generator(config)
    reporter.set_scan_result(scan_result)
    
    run_parser(parser, scan_result, reporter)
    
    report_path = run_reporter(reporter)
    
    if report_path:
        print()
        print_info("=" * 60)
        print_info("扫描完成！")
        print_info(f"请查看报告: {report_path}")
        print_info("=" * 60)
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
