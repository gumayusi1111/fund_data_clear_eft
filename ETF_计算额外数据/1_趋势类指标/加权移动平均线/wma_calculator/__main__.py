#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA计算器模块入口点
=================

支持 python -m wma_calculator 的执行方式
从父目录导入主程序
"""

import sys
import os

# 添加父目录到路径，以便导入主程序
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # 导入并执行主程序
    from wma_main import main
    main() 