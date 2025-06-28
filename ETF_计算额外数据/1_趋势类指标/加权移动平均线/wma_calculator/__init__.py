#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA计算器模块化包
==============

📦 模块架构:
- config: 配置管理
- data_reader: 数据读取器
- wma_engine: WMA计算引擎  
- signal_analyzer: 信号分析器
- result_processor: 结果处理器
- file_manager: 文件管理器
- controller: 主控制器
- utils: 工具函数

🛡️ 设计原则:
- 高内聚低耦合
- 单一职责原则
- 便于测试和维护
"""

__version__ = "1.0.0"
__author__ = "ETF数据处理系统"

# 导入主要组件
from .config import WMAConfig
from .data_reader import ETFDataReader
from .wma_engine import WMAEngine
from .signal_analyzer import SignalAnalyzer
from .result_processor import ResultProcessor
from .file_manager import FileManager
from .controller import WMAController

# 导出主要接口
__all__ = [
    'WMAConfig',
    'ETFDataReader', 
    'WMAEngine',
    'SignalAnalyzer',
    'ResultProcessor',
    'FileManager',
    'WMAController'
] 