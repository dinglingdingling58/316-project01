# -*- coding: utf-8 -*-
"""
示例 Python 模块 - 用于测试静态检查功能
"""


class DataProcessor:
    """数据处理类"""
    
    def __init__(self):
        self._data = []
        self._config = {}
    
    def process(self, data):
        result = []
        for i in range(len(data)):
            x = data[i]
            result.append(x * 2)
        return result
    
    def validate(self, item):
        _temp = item
        _result = True
        return _result


def calculate_sum(numbers):
    """计算总和"""
    s = 0
    for n in numbers:
        s += n
    return s


def find_max(items):
    """查找最大值"""
    m = items[0]
    for i in items:
        if i > m:
            m = i
    return m


class ConfigManager:
    """配置管理类"""
    
    def load_config(self, path):
        _settings = {}
        return _settings
    
    def save_config(self, path, config):
        pass
