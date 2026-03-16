# -*- coding: utf-8 -*-
"""
配置模块 - 定义常量、支持的后缀列表、配置读取功能
"""
import os
from typing import List, Dict, Optional

INPUT_DIR: str = "./source_data/"
OUTPUT_DIR: str = "./output_build/"
REPORT_FILENAME: str = "analysis-report.txt"
DO_NOT_TOUCH_FILE: str = ".do_not_touch.cfg"

SUPPORTED_EXTENSIONS: Dict[str, str] = {
    ".md": "markdown",
    ".py": "python",
    ".txt": "text",
    ".rst": "restructuredtext",
    ".html": "html",
}

MARKDOWN_HEADING_PATTERNS: Dict[int, str] = {
    1: r"^#\s+.+$",
    2: r"^##\s+.+$",
    3: r"^###\s+.+$",
    4: r"^####\s+.+$",
}

PYTHON_SINGLE_LETTER_VARS: List[str] = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]

PYTHON_DUNDER_NAMES: List[str] = [
    '__init__', '__new__', '__del__', '__repr__', '__str__', '__bytes__',
    '__format__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',
    '__hash__', '__bool__', '__getattr__', '__getattribute__', '__setattr__',
    '__delattr__', '__dir__', '__get__', '__set__', '__delete__', '__call__',
    '__len__', '__length_hint__', '__getitem__', '__setitem__', '__delitem__',
    '__iter__', '__reversed__', '__contains__', '__add__', '__sub__', '__mul__',
    '__truediv__', '__floordiv__', '__mod__', '__divmod__', '__pow__',
    '__name__', '__doc__', '__class__', '__module__', '__dict__', '__weakref__',
    '__all__', '__file__', '__package__', '__path__', '__version__', '__author__',
    '__enter__', '__exit__', '__main__', '__builtins__', '__import__'
]


class Config:
    """配置类，管理程序配置"""
    
    def __init__(self, input_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self._input_dir: str = input_dir if input_dir else INPUT_DIR
        self._output_dir: str = output_dir if output_dir else OUTPUT_DIR
        self._do_not_touch_dirs: List[str] = []
        self._errors: List[str] = []
    
    @property
    def input_dir(self) -> str:
        return self._input_dir
    
    @property
    def output_dir(self) -> str:
        return self._output_dir
    
    @property
    def do_not_touch_dirs(self) -> List[str]:
        return self._do_not_touch_dirs.copy()
    
    @property
    def errors(self) -> List[str]:
        return self._errors.copy()
    
    def add_error(self, error_msg: str) -> None:
        self._errors.append(error_msg)
    
    def load_do_not_touch_config(self) -> bool:
        config_path = os.path.join(self._input_dir, DO_NOT_TOUCH_FILE)
        if not os.path.exists(config_path):
            return True
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    full_path = os.path.join(self._input_dir, line)
                    self._do_not_touch_dirs.append(os.path.normpath(full_path))
            return True
        except Exception as e:
            self.add_error(f"读取配置文件 {DO_NOT_TOUCH_FILE} 失败: {str(e)}")
            return False
    
    def is_do_not_touch_dir(self, dir_path: str) -> bool:
        normalized_path = os.path.normpath(dir_path)
        for forbidden_dir in self._do_not_touch_dirs:
            if normalized_path.startswith(forbidden_dir):
                return True
        return False
    
    def get_supported_extensions(self) -> List[str]:
        return list(SUPPORTED_EXTENSIONS.keys())
    
    def get_file_type(self, extension: str) -> Optional[str]:
        ext_lower = extension.lower()
        return SUPPORTED_EXTENSIONS.get(ext_lower)


def create_config(input_dir: Optional[str] = None, output_dir: Optional[str] = None) -> Config:
    """创建配置实例的工厂函数"""
    return Config(input_dir, output_dir)
