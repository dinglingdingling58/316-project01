"""
示例 Python 模块
用于测试 Python 静态检查功能
"""

# 一些单字母变量（应该被检测出来）
a = 10
b = 20
x = a + b
y = x * 2

# 不规范的私有变量命名（应该被检测出来）
_private_var = 100
_internal = "test"

# 正确的命名
MAX_SIZE = 100
default_value = None


class SampleClass:
    """示例类。"""
    
    def __init__(self):
        self.name = "sample"
        self._value = 0
    
    def calculate(self, i, j):
        """
        计算方法（使用了单字母参数）。
        
        Args:
            i: 第一个参数
            j: 第二个参数
        """
        result = i + j
        return result
    
    def process_data(self, data):
        """处理数据。"""
        if not data:
            return None
        
        # 使用单字母变量
        n = len(data)
        s = sum(data)
        
        return s / n if n > 0 else 0


def helper_function():
    """辅助函数。"""
    return True


def another_function(x, y, z):
    """
    另一个函数（使用了单字母参数）。
    
    Args:
        x: X 坐标
        y: Y 坐标
        z: Z 坐标
    """
    return x + y + z
