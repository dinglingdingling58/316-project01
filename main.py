import os
import sys
from typing import List, Dict, Any

from utils.util_config import INPUT_DIR, OUTPUT_DIR, read_protected_config
from utils.util_validators import validate_input_directory
from core_scanner import scan_directory, read_file_content
from core_parser import parse_file
from report_builder import generate_report


def main() -> int:
    try:
        read_protected_config()
    except Exception:
        pass

    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
    except Exception:
        pass

    if not validate_input_directory(INPUT_DIR):
        try:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR, exist_ok=True)
            report_path = os.path.join(OUTPUT_DIR, 'analysis-report.txt')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"输入目录不存在或无效: {INPUT_DIR}")
        except Exception:
            pass
        return 1

    all_results: List[Dict[str, Any]] = []

    try:
        files_info = scan_directory(INPUT_DIR)
    except Exception:
        files_info = []

    for file_info in files_info:
        try:
            content = read_file_content(file_info['path'])
            parse_result = parse_file(file_info['path'], content, file_info['extension'])
            all_results.append({
                'file_info': file_info,
                'parse_result': parse_result
            })
        except Exception as e:
            all_results.append({
                'file_info': file_info,
                'parse_result': {'error': str(e) or '处理失败', 'total_lines': 0}
            })

    try:
        generate_report(all_results, OUTPUT_DIR)
    except Exception:
        pass

    return 0


if __name__ == '__main__':
    sys.exit(main())
