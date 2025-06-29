#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD指标组合计算器模块
====================

模块化的MACD指标计算系统，包含：
- DIF线计算 (EMA12 - EMA26)
- DEA线计算 (DIF的9日EMA)
- MACD柱计算 ((DIF - DEA) × 2)
- 金叉死叉信号判断
- 零轴位置分析
- 背离检测等高级功能

Author: AI Assistant
Date: 2025-01-27
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

# 导入主要组件
from .config import MACDConfig
from .macd_engine import MACDEngine
from .signal_analyzer import MACDSignalAnalyzer
from .data_processor import MACDDataProcessor
from .result_processor import MACDResultProcessor
from .controller import MACDController

__all__ = [
    'MACDConfig',
    'MACDEngine', 
    'MACDSignalAnalyzer',
    'MACDDataProcessor',
    'MACDResultProcessor',
    'MACDController'
] 