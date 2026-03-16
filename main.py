"""
主入口模块 - 唯一入口，负责参数解析与流程调度。

路径约束：
- 输入目录： ./source_data/
- 输出目录： ./output_build/
- 禁止在 ./source_data/ 目录下创建、修改、删除、重命名任何文件

技术约束：
- 只使用 Python 3.9 ~ 3.11 标准库
- 不使用 pathlib（只用 os / os.path）
- 错误处理要完备（使用 try-except），但不要打印堆栈，要优雅记录到报告中
"""

import sys
import os
import argparse
from typing import List, Dict, Any, Optional

# 确保可以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import (
    INPUT_DIRECTORY,
    OUTPUT_DIRECTORY,
    REPORT_FILENAME,
    SUPPORTED_EXTENSIONS,
    read_protected_marker,
    ensure_output_directory,
)
from utils.validators import is_valid_module_filename
from core_scanner import FileScanner, ScanResult
from core_parser import ContentParser
from report_generator import ReportGenerator


# =============================================================================
# 版本信息
# =============================================================================

__version__ = '1.0.0'
__author__ = 'Document Scanner Tool'


# =============================================================================
# 参数解析
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数。
    
    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        prog='doc_scanner',
        description='多格式文档静态结构扫描与元数据提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py                    # 使用默认配置扫描
  python main.py -v                 # 显示详细输出
  python main.py --input ./docs     # 指定输入目录
  python main.py --output ./reports # 指定输出目录

路径约束:
  - 输入目录: ./source_data/
  - 输出目录: ./output_build/
  - 禁止修改 source_data 目录下的任何文件
        '''
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default=INPUT_DIRECTORY,
        help=f'输入目录路径 (默认: {INPUT_DIRECTORY})'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=OUTPUT_DIRECTORY,
        help=f'输出目录路径 (默认: {OUTPUT_DIRECTORY})'
    )
    
    parser.add_argument(
        '-r', '--report',
        type=str,
        default=REPORT_FILENAME,
        help=f'报告文件名 (默认: {REPORT_FILENAME})'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        type=str,
        nargs='+',
        default=None,
        help=f'要处理的文件扩展名 (默认: {", ".join(sorted(SUPPORTED_EXTENSIONS))})'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='不生成报告文件，仅输出到控制台'
    )
    
    return parser.parse_args()


# =============================================================================
# 验证函数
# =============================================================================

def validate_environment(args: argparse.Namespace) -> List[str]:
    """
    验证运行环境。
    
    Args:
        args: 命令行参数
        
    Returns:
        错误信息列表
    """
    errors = []
    
    # 检查输入目录
    input_dir = os.path.abspath(args.input)
    if not os.path.exists(input_dir):
        errors.append(f"输入目录不存在: {input_dir}")
    elif not os.path.isdir(input_dir):
        errors.append(f"输入路径不是目录: {input_dir}")
    
    # 检查输出目录（如果不存在会尝试创建）
    output_dir = os.path.abspath(args.output)
    if os.path.exists(output_dir) and not os.path.isdir(output_dir):
        errors.append(f"输出路径存在但不是目录: {output_dir}")
    
    # 检查扩展名
    if args.extensions:
        invalid_exts = []
        for ext in args.extensions:
            # 规范化扩展名
            if not ext.startswith('.'):
                ext = '.' + ext
            if ext.lower() not in SUPPORTED_EXTENSIONS:
                invalid_exts.append(ext)
        
        if invalid_exts:
            errors.append(f"不支持的文件扩展名: {', '.join(invalid_exts)}")
            errors.append(f"支持的扩展名: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    
    return errors


# =============================================================================
# 核心流程
# =============================================================================

class DocumentScannerApp:
    """文档扫描应用程序主类。"""
    
    def __init__(self, args: argparse.Namespace):
        """
        初始化应用程序。
        
        Args:
            args: 命令行参数
        """
        self.args = args
        self.input_dir = os.path.abspath(args.input)
        self.output_dir = os.path.abspath(args.output)
        self.verbose = args.verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def log(self, message: str) -> None:
        """
        输出日志信息。
        
        Args:
            message: 日志消息
        """
        if self.verbose:
            print(message)
    
    def run(self) -> int:
        """
        运行应用程序。
        
        Returns:
            退出码 (0 表示成功)
        """
        print("=" * 60)
        print("文档静态结构扫描与元数据提取工具")
        print("=" * 60)
        print()
        
        # 验证环境
        env_errors = validate_environment(self.args)
        if env_errors:
            print("环境验证失败:")
            for error in env_errors:
                print(f"  [错误] {error}")
            return 1
        
        self.log(f"输入目录: {self.input_dir}")
        self.log(f"输出目录: {self.output_dir}")
        self.log("")
        
        # 读取配置
        config = read_protected_marker()
        if config.get('marker_exists'):
            self.log(f"检测到保护标记文件: .do_not_touch.cfg")
            self.log(f"受保护路径: {config.get('protected_paths', [])}")
            self.log("")
        
        # 步骤 1: 扫描文件
        print("[1/3] 正在扫描文件...")
        scan_result = self._scan_files()
        
        if scan_result.files_scanned == 0:
            print("警告: 未找到可扫描的文件")
            return 0
        
        print(f"  发现文件: {scan_result.total_files_found}")
        print(f"  已扫描: {scan_result.files_scanned}")
        print(f"  已跳过: {scan_result.files_skipped}")
        print()
        
        # 步骤 2: 解析内容
        print("[2/3] 正在解析内容...")
        parse_results = self._parse_files(scan_result)
        print(f"  已解析: {len(parse_results)} 个文件")
        print()
        
        # 步骤 3: 生成报告
        print("[3/3] 正在生成报告...")
        
        # 收集扫描统计
        scanner = FileScanner(self.input_dir)
        scan_stats = scanner.get_statistics(scan_result)
        
        # 添加文件大小信息
        for file_info in scan_result.file_list:
            for result in parse_results:
                if result.get('filepath') == file_info.absolute_path:
                    result['size_bytes'] = file_info.size_bytes
                    break
        
        # 生成报告
        generator = ReportGenerator(self.output_dir)
        success, content = generator.generate_and_save(
            scan_stats,
            parse_results,
            self.errors + scan_result.errors,
        )
        
        if success:
            report_path = os.path.join(self.output_dir, self.args.report)
            print(f"  报告已保存: {report_path}")
            
            if not self.args.no_report:
                # 同时输出到控制台
                print()
                print("=" * 60)
                print("报告预览")
                print("=" * 60)
                print(content[:2000] + "..." if len(content) > 2000 else content)
        else:
            print(f"  [错误] 生成报告失败: {content}")
            return 1
        
        print()
        print("=" * 60)
        print("扫描完成")
        print("=" * 60)
        
        return 0
    
    def _scan_files(self) -> ScanResult:
        """
        扫描文件。
        
        Returns:
            扫描结果
        """
        extensions = None
        if self.args.extensions:
            extensions = [
                ext if ext.startswith('.') else '.' + ext
                for ext in self.args.extensions
            ]
        
        scanner = FileScanner(self.input_dir, extensions)
        
        def progress_callback(filepath: str) -> None:
            """进度回调。"""
            if self.verbose:
                filename = os.path.basename(filepath)
                print(f"  扫描: {filename}")
        
        return scanner.scan(progress_callback)
    
    def _parse_files(self, scan_result: ScanResult) -> List[Dict[str, Any]]:
        """
        解析文件内容。
        
        Args:
            scan_result: 扫描结果
            
        Returns:
            解析结果列表
        """
        results = []
        total = len(scan_result.file_list)
        
        for i, file_info in enumerate(scan_result.file_list, 1):
            if self.verbose:
                print(f"  解析 [{i}/{total}]: {file_info.filename}")
            
            # 跳过二进制文件
            if file_info.is_binary:
                results.append({
                    'filepath': file_info.absolute_path,
                    'extension': file_info.extension,
                    'size_bytes': file_info.size_bytes,
                    'success': False,
                    'data': None,
                    'error': '二进制文件，跳过解析',
                })
                continue
            
            # 解析文件
            result = ContentParser.parse_file(
                file_info.absolute_path,
                file_info.extension,
            )
            result['size_bytes'] = file_info.size_bytes
            results.append(result)
            
            if not result['success'] and result.get('error'):
                self.warnings.append(f"解析失败 {file_info.filename}: {result['error']}")
        
        return results


# =============================================================================
# 主函数
# =============================================================================

def main() -> int:
    """
    主入口函数。
    
    Returns:
        退出码
    """
    try:
        args = parse_arguments()
        app = DocumentScannerApp(args)
        return app.run()
    except KeyboardInterrupt:
        print()
        print("操作已取消")
        return 130
    except Exception as e:
        print()
        print(f"发生错误: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
