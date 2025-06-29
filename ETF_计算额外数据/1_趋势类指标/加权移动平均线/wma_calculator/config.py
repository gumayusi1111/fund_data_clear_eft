#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA配置管理模块 - 科学严谨版 + 系统差异化
==============================

负责管理WMA计算器的所有配置项
🔬 科学标准: 复权类型选择科学性、数据处理严谨性
🎯 系统特性: WMA对近期价格最敏感，需要更严格的参数控制
"""

import os
from typing import List, Dict, Optional


class WMAConfig:
    """WMA计算配置管理器 - 科学严谨版 + 系统差异化"""
    
    # 复权类型映射 - 科学评估
    ADJ_TYPES = {
        "前复权": "0_ETF日K(前复权)",    # 🔬 推荐: 技术分析最优选择
        "后复权": "0_ETF日K(后复权)",    # ⚠️ 谨慎: 价格会变动，影响历史分析
        "除权": "0_ETF日K(除权)"        # ❌ 不推荐: 价格跳跃，破坏指标连续性
    }
    
    # 🎯 WMA系统专属参数设置（最敏感系统）
    WMA_SYSTEM_PARAMS = {
        'name': 'WMA',
        'sensitivity_level': 'HIGHEST',  # 最高敏感度
        'base_threshold': 0.20,          # 比标准低：更严格筛选假信号
        'tolerance_ratio': 0.25,         # 最严格的容错：只允许25%次要均线反向
        'volume_factor': 1.20,           # 量能确认阈值：5日均量/20日均量 > 1.2
        'signal_decay': 0.15,            # 信号衰减最快：WMA变化快，信号持续性差
        'quality_bonus_threshold': 2.5,  # 高质量信号奖励阈值：差距>2.5%
        'noise_filter': 0.15,            # 更严格的噪音过滤：<0.15%视为噪音
        'description': 'WMA对近期价格最敏感，变化最快，需要最严格的参数控制假信号'
    }
    
    # 🔬 科学复权评估
    ADJ_TYPE_SCIENTIFIC_EVALUATION = {
        "前复权": {
            "scientific_score": 95,
            "recommendation": "强烈推荐",
            "pros": ["价格连续性好", "适合技术指标", "历史数据稳定"],
            "cons": ["历史价格非实际价格"],
            "use_cases": ["技术分析", "WMA计算", "趋势判断"]
        },
        "后复权": {
            "scientific_score": 60,
            "recommendation": "谨慎使用",
            "pros": ["基于当前价格", "便于理解收益"],
            "cons": ["历史价格会变化", "影响技术指标", "不利于回测"],
            "use_cases": ["收益计算", "资产配置"]
        },
        "除权": {
            "scientific_score": 30,
            "recommendation": "不推荐",
            "pros": ["实际交易价格"],
            "cons": ["价格跳跃严重", "破坏指标连续性", "影响WMA准确性"],
            "use_cases": ["查看实际价格"]
        }
    }
    
    # 默认WMA周期 - 科学选择
    DEFAULT_WMA_PERIODS = [3, 5, 10, 20]  # 🔬 涵盖短中长期，符合技术分析标准
    
    # 默认ETF代码（股票型ETF，价格变化明显）
    DEFAULT_ETF_CODE = "510050.SH"  # 上证50ETF - 流动性好，代表性强
    
    # 🔬 数据策略: 使用所有可用数据，不人为限制
    # SCIENTIFIC_DATA_LIMIT = 50  # 已禁用：不再限制数据行数
    
    def __init__(self, adj_type: str = "前复权", wma_periods: Optional[List[int]] = None):
        """
        初始化配置 - 科学严谨版 + 系统差异化
        
        Args:
            adj_type: 复权类型
            wma_periods: WMA周期列表
        """
        self.adj_type = self._validate_and_recommend_adj_type(adj_type)
        self.wma_periods = wma_periods or self.DEFAULT_WMA_PERIODS.copy()
        self.max_period = max(self.wma_periods)
        
        # 🎯 WMA系统专属参数
        self.system_params = self.WMA_SYSTEM_PARAMS.copy()
        
        # 🔬 数据策略: 使用所有可用数据，不人为限制
        self.required_rows = None  # 不限制数据行数
        
        # 🔬 数据策略验证: 只需确保有足够数据计算最大周期
        # 不再人为限制数据量，让系统自动适应ETF的实际数据情况
        
        # 数据路径配置 - 🔬 科学路径计算
        # 智能路径检测：根据当前目录自动找到正确路径
        current_dir = os.getcwd()
        
        if "加权移动平均线" in current_dir:
            # 从加权移动平均线目录运行: ../../../ETF日更
            self.base_data_path = "../../../ETF日更"
            self.wma_script_dir = "."  # 当前就是脚本目录
        elif "data_clear" in current_dir and current_dir.endswith("data_clear"):
            # 从项目根目录运行: ./ETF日更
            self.base_data_path = "./ETF日更"
            self.wma_script_dir = "./ETF_计算额外数据/1_趋势类指标/加权移动平均线"  # 脚本所在目录
        else:
            # 默认相对路径
            self.base_data_path = "./ETF日更"
            self.wma_script_dir = "."
        
        self.data_path = os.path.join(self.base_data_path, self.ADJ_TYPES[self.adj_type])
        
        # 🔬 输出配置 - 确保输出始终在WMA脚本目录下
        self.default_output_dir = os.path.join(self.wma_script_dir, "data")
        
        print(f"🔬 WMA配置初始化完成 (科学严谨版 + 系统差异化):")
        print(f"   📈 复权类型: {self.adj_type} (科学评分: {self.get_scientific_score()}/100)")
        print(f"   🎯 WMA周期: {self.wma_periods}")
        print(f"   ⚙️ 系统特性: {self.system_params['description']}")
        print(f"   📊 系统参数: 基准阈值={self.system_params['base_threshold']}%, 容错率={self.system_params['tolerance_ratio']}")
        print(f"   📊 数据策略: 使用所有可用数据，不限制行数")
        print(f"   📁 数据路径: {self.data_path}")
        
        # 🔬 科学建议
        self._provide_scientific_recommendation()
    
    def get_system_thresholds(self) -> Dict[str, float]:
        """
        获取WMA系统专属的阈值参数
        
        Returns:
            Dict: 系统阈值配置
        """
        return {
            'minimal': self.system_params['base_threshold'],     # 0.20% - 更严格
            'moderate': self.system_params['base_threshold'] * 3, # 0.60% - 对应更严格
            'strong': self.system_params['base_threshold'] * 6,   # 1.20% - 对应更严格  
            'noise_filter': self.system_params['noise_filter']   # 0.15% - 更严格噪音过滤
        }
    
    def get_system_score_weights(self) -> Dict[str, float]:
        """
        获取WMA系统专属的评分权重
        
        Returns:
            Dict: 系统评分权重
        """
        # WMA变化快，降低评分权重避免过度交易
        return {
            '强势': 1.0,    # 降低权重：从1.2降到1.0
            '中等': 0.6,    # 降低权重：从0.8降到0.6
            '温和': 0.3,    # 降低权重：从0.4降到0.3
            '微弱': 0.05    # 大幅降低：从0.1降到0.05
        }
    
    def get_volume_threshold(self) -> float:
        """获取WMA系统的量能确认阈值"""
        return self.system_params['volume_factor']
    
    def get_tolerance_ratio(self) -> float:
        """获取WMA系统的容错比例"""
        return self.system_params['tolerance_ratio']
    
    def _validate_and_recommend_adj_type(self, adj_type: str) -> str:
        """
        验证并推荐复权类型 - 科学评估
        
        Args:
            adj_type: 输入的复权类型
            
        Returns:
            str: 验证后的复权类型
        """
        if adj_type not in self.ADJ_TYPES:
            print(f"❌ 科学错误: 不支持的复权类型: {adj_type}")
            print(f"💡 支持的类型: {list(self.ADJ_TYPES.keys())}")
            adj_type = "前复权"  # 默认使用科学推荐
            print(f"🔬 已自动使用科学推荐类型: {adj_type}")
        
        return adj_type
    
    def get_scientific_score(self) -> int:
        """获取当前复权类型的科学评分"""
        return self.ADJ_TYPE_SCIENTIFIC_EVALUATION[self.adj_type]["scientific_score"]
    
    def _provide_scientific_recommendation(self):
        """提供科学建议"""
        evaluation = self.ADJ_TYPE_SCIENTIFIC_EVALUATION[self.adj_type]
        
        if evaluation["scientific_score"] < 70:
            print(f"⚠️  科学建议: 当前复权类型'{self.adj_type}'科学评分较低")
            print(f"🔬 推荐使用: '前复权' (科学评分: 95/100)")
            print(f"💡 理由: 前复权最适合WMA等技术指标计算")
    
    def get_scientific_evaluation(self) -> Dict:
        """获取复权类型的科学评估"""
        return self.ADJ_TYPE_SCIENTIFIC_EVALUATION[self.adj_type]
    
    def validate_data_path(self) -> bool:
        """验证数据路径是否存在"""
        if os.path.exists(self.data_path):
            print(f"🔍 数据路径验证: {self.data_path} ✅")
            return True
        else:
            print(f"❌ 数据路径不存在: {self.data_path}")
            print("💡 提示: 请检查脚本运行位置或数据文件路径")
            return False
    
    def get_file_path(self, etf_code: str) -> str:
        """获取ETF数据文件的完整路径"""
        return os.path.join(self.data_path, f"{etf_code}.csv")
    
    def get_adj_folder_name(self) -> str:
        """获取复权文件夹名称"""
        return self.ADJ_TYPES[self.adj_type]
    
    def to_dict(self) -> Dict:
        """将配置转换为字典格式"""
        return {
            'adj_type': self.adj_type,
            'scientific_score': self.get_scientific_score(),
            'scientific_evaluation': self.get_scientific_evaluation(),
            'wma_periods': self.wma_periods,
            'max_period': self.max_period,
            'required_rows': self.required_rows,
            'data_path': self.data_path,
            'system_params': self.system_params,
            'system_thresholds': self.get_system_thresholds(),
            'system_score_weights': self.get_system_score_weights(),
            'optimization': f'WMA系统专属参数：最严格控制 (基准{self.system_params["base_threshold"]}%)'
        } 