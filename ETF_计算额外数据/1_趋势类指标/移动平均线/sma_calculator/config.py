#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA配置管理模块
=============

专门管理简单移动平均线的配置参数
专注于中短线交易指标，不包含长线指标
"""

import os
from typing import List, Optional


class SMAConfig:
    """SMA配置管理类 - 中短线专版"""
    
    def __init__(self, adj_type: str = "前复权", sma_periods: Optional[List[int]] = None):
        """
        初始化SMA配置
        
        Args:
            adj_type: 复权类型 ("前复权", "后复权", "除权")
            sma_periods: SMA周期列表，None时使用默认中短线配置
        """
        print("⚙️  SMA配置初始化...")
        
        # 复权类型配置
        self.adj_type = adj_type
        self.adj_type_mapping = {
            "前复权": "0_ETF日K(前复权)",
            "后复权": "0_ETF日K(后复权)", 
            "除权": "0_ETF日K(除权)"
        }
        
        # 🎯 中短线SMA周期配置（用户要求）
        if sma_periods is None:
            self.sma_periods = [5, 10, 20, 60]  # 专注中短线，移除120, 250
        else:
            self.sma_periods = sma_periods
        
        # 数据要求
        self.required_rows = 70  # SMA60需要60行，留10行缓冲
        
        # 路径配置
        self._setup_paths()
        
        print(f"   ✅ 复权类型: {self.adj_type}")
        print(f"   📊 SMA周期: {self.sma_periods} (中短线专版)")
        print(f"   📁 数据目录: {self.data_dir}")
        print(f"   📄 数据要求: {self.required_rows}行")
        
    def _setup_paths(self):
        """智能路径配置"""
        # 获取当前脚本的基础目录
        current_dir = os.getcwd()
        
        # 智能检测项目根目录
        if "ETF_计算额外数据" in current_dir:
            # 当前在项目内部
            project_root = current_dir.split("ETF_计算额外数据")[0]
        else:
            # 假设当前目录就是项目根目录
            project_root = current_dir
            
        # 构建数据目录路径
        self.data_dir = os.path.join(project_root, "ETF日更", self.adj_type_mapping[self.adj_type])
        
        # 🔬 智能输出目录配置 - 模仿WMA结构
        # 基础输出目录，具体门槛目录在运行时确定
        self.default_output_dir = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "data"
        )
        
        print(f"   🔍 项目根目录: {project_root}")
        print(f"   📂 数据目录: {self.data_dir}")
        
    def validate_data_path(self) -> bool:
        """
        验证数据路径是否存在
        
        Returns:
            bool: 路径是否有效
        """
        if os.path.exists(self.data_dir):
            file_count = len([f for f in os.listdir(self.data_dir) if f.endswith('.csv')])
            print(f"   ✅ 数据路径验证成功，找到 {file_count} 个CSV文件")
            return True
        else:
            print(f"   ❌ 数据路径不存在: {self.data_dir}")
            return False
    
    def get_etf_file_path(self, etf_code: str) -> str:
        """
        获取ETF数据文件路径
        
        Args:
            etf_code: ETF代码
            
        Returns:
            str: 文件路径
        """
        # 标准化ETF代码格式
        if not etf_code.endswith(('.SH', '.SZ')):
            # 如果没有后缀，需要智能判断
            if etf_code.startswith('5'):
                etf_code += '.SH'
            elif etf_code.startswith('1'):
                etf_code += '.SZ'
        
        filename = f"{etf_code}.csv"
        return os.path.join(self.data_dir, filename)
    
    def get_sma_display_info(self) -> str:
        """
        获取SMA配置的显示信息
        
        Returns:
            str: 配置描述
        """
        period_desc = ", ".join([f"MA{p}" for p in self.sma_periods])
        return f"SMA配置 ({self.adj_type}): {period_desc}"
        
    @property
    def max_period(self) -> int:
        """获取最大周期"""
        return max(self.sma_periods) if self.sma_periods else 60 