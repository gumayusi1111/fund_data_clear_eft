#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA配置管理模块 - 系统差异化版
=============

专门管理简单移动平均线的配置参数
🎯 系统特性: SMA最平滑稳定，作为标准参数基准
专注于中短线交易指标，不包含长线指标
"""

import os
from typing import List, Optional, Dict


class SMAConfig:
    """SMA配置管理类 - 中短线专版 + 系统差异化"""
    
    # 🎯 SMA系统专属参数设置（标准基准系统）
    SMA_SYSTEM_PARAMS = {
        'name': 'SMA',
        'sensitivity_level': 'STANDARD',  # 标准敏感度
        'base_threshold': 0.25,           # 标准基准阈值：平衡敏感性和稳定性
        'tolerance_ratio': 0.33,          # 标准容错：允许33%次要均线反向
        'volume_factor': 1.15,            # 标准量能确认：5日均量/20日均量 > 1.15
        'signal_decay': 0.25,             # 标准信号衰减：SMA信号最持久
        'quality_bonus_threshold': 2.0,   # 标准质量信号奖励阈值：差距>2.0%
        'noise_filter': 0.20,             # 标准噪音过滤：<0.20%视为噪音
        'description': 'SMA最平滑稳定，具有很好的噪音过滤，适合作为标准参数基准'
    }
    
    def __init__(self, adj_type: str = "前复权", sma_periods: Optional[List[int]] = None):
        """
        初始化SMA配置 - 系统差异化版
        
        Args:
            adj_type: 复权类型 ("前复权", "后复权", "除权")
            sma_periods: SMA周期列表，None时使用默认中短线配置
        """
        print("⚙️  SMA配置初始化 (系统差异化版)...")
        
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
        
        # 🎯 SMA系统专属参数
        self.system_params = self.SMA_SYSTEM_PARAMS.copy()
        
        # 数据要求 - 🔬 使用所有可用数据，不限制行数
        self.required_rows = None  # 不限制行数，使用ETF的所有历史数据
        
        # 路径配置
        self._setup_paths()
        
        print(f"   ✅ 复权类型: {self.adj_type}")
        print(f"   📊 SMA周期: {self.sma_periods} (中短线专版)")
        print(f"   ⚙️ 系统特性: {self.system_params['description']}")
        print(f"   📊 系统参数: 基准阈值={self.system_params['base_threshold']}%, 容错率={self.system_params['tolerance_ratio']}")
        print(f"   📁 数据目录: {self.data_dir}")
        if self.required_rows is not None:
            print(f"   📄 数据要求: {self.required_rows}行")
        else:
            print(f"   📄 数据策略: 使用所有可用历史数据")
        
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
        
    def get_system_thresholds(self) -> Dict[str, float]:
        """
        获取SMA系统专属的阈值参数（标准基准）
        
        Returns:
            Dict: 系统阈值配置
        """
        return {
            'minimal': self.system_params['base_threshold'],     # 0.25% - 标准基准
            'moderate': self.system_params['base_threshold'] * 3.2, # 0.80% - 标准比例
            'strong': self.system_params['base_threshold'] * 6,   # 1.50% - 标准比例  
            'noise_filter': self.system_params['noise_filter']   # 0.20% - 标准噪音过滤
        }
    
    def get_system_score_weights(self) -> Dict[str, float]:
        """
        获取SMA系统专属的评分权重（标准基准）
        
        Returns:
            Dict: 系统评分权重
        """
        # SMA最稳定，使用标准权重作为基准
        return {
            '强势': 1.2,    # 标准权重
            '中等': 0.8,    # 标准权重
            '温和': 0.4,    # 标准权重
            '微弱': 0.1     # 标准权重
        }
    
    def get_volume_threshold(self) -> float:
        """获取SMA系统的量能确认阈值"""
        return self.system_params['volume_factor']
    
    def get_tolerance_ratio(self) -> float:
        """获取SMA系统的容错比例"""
        return self.system_params['tolerance_ratio']
        
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
        
    def to_dict(self) -> Dict:
        """将配置转换为字典格式"""
        return {
            'adj_type': self.adj_type,
            'sma_periods': self.sma_periods,
            'max_period': self.max_period,
            'required_rows': self.required_rows,
            'data_dir': self.data_dir,
            'system_params': self.system_params,
            'system_thresholds': self.get_system_thresholds(),
            'system_score_weights': self.get_system_score_weights(),
            'optimization': f'SMA系统专属参数：标准基准控制 (基准{self.system_params["base_threshold"]}%)'
        } 