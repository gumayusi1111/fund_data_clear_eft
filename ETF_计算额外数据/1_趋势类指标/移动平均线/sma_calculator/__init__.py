#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA计算器模块化包
===============

📦 模块架构:
- config: 配置管理
- data_reader: 数据读取器
- sma_engine: SMA计算引擎  
- signal_analyzer: 信号分析器
- result_processor: 结果处理器
- file_manager: 文件管理器
- controller: 主控制器

🛡️ 设计原则:
- 高内聚低耦合
- 专注中短线指标
- 简洁高效
"""

__version__ = "1.0.0"
__author__ = "ETF数据处理系统"

# 导入主要组件
from .config import SMAConfig
from .data_reader import ETFDataReader
from .sma_engine import SMAEngine
from .signal_analyzer import SignalAnalyzer
from .result_processor import ResultProcessor
from .file_manager import FileManager
from .controller import SMAController

# 导出主要接口
__all__ = [
    'SMAConfig',
    'ETFDataReader', 
    'SMAEngine',
    'SignalAnalyzer',
    'ResultProcessor',
    'FileManager',
    'SMAController'
] 