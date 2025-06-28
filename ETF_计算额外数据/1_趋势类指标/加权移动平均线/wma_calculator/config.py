#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA配置管理模块 - 科学严谨版
==============================

负责管理WMA计算器的所有配置项
🔬 科学标准: 复权类型选择科学性、数据处理严谨性

复权类型科学评估：
=================
🔬 前复权 (推荐): 
   - 适用场景: 技术分析、趋势判断、指标计算
   - 优势: 消除除权影响，价格连续性好，适合WMA等技术指标
   - 科学原理: 历史价格按复权因子调整，确保指标计算的连续性
   
🔬 后复权:
   - 适用场景: 投资收益计算、资产配置分析
   - 优势: 基于当前价格推算，便于理解投资收益
   - 局限: 历史价格会随时间变化，不适合技术指标
   
🔬 除权 (不推荐用于技术分析):
   - 适用场景: 查看实际交易价格
   - 局限: 价格跳跃，破坏指标连续性，影响WMA准确性

🎯 结论: 对于WMA技术指标，科学选择为"前复权"
"""

import os
from typing import List, Dict, Optional


class WMAConfig:
    """WMA计算配置管理器 - 科学严谨版"""
    
    # 复权类型映射 - 科学评估
    ADJ_TYPES = {
        "前复权": "0_ETF日K(前复权)",    # 🔬 推荐: 技术分析最优选择
        "后复权": "0_ETF日K(后复权)",    # ⚠️ 谨慎: 价格会变动，影响历史分析
        "除权": "0_ETF日K(除权)"        # ❌ 不推荐: 价格跳跃，破坏指标连续性
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
    
    # 🔬 科学数据限制: 严格50行 (WMA20需要20行，30行缓冲)
    SCIENTIFIC_DATA_LIMIT = 50
    
    def __init__(self, adj_type: str = "前复权", wma_periods: Optional[List[int]] = None):
        """
        初始化配置 - 科学严谨版
        
        Args:
            adj_type: 复权类型
            wma_periods: WMA周期列表
        """
        self.adj_type = self._validate_and_recommend_adj_type(adj_type)
        self.wma_periods = wma_periods or self.DEFAULT_WMA_PERIODS.copy()
        self.max_period = max(self.wma_periods)
        
        # 🔬 科学数据限制: 严格控制在50行
        self.required_rows = self.SCIENTIFIC_DATA_LIMIT
        
        # 🔬 科学验证: 确保数据足够
        if self.max_period > self.required_rows - 10:
            print(f"⚠️  科学警告: 最大周期{self.max_period}接近数据限制{self.required_rows}")
            print(f"🔬 建议: 保持WMA周期≤20，数据行数=50")
        
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
        
        print(f"🔬 配置初始化完成 (科学严谨版):")
        print(f"   📈 复权类型: {self.adj_type} (科学评分: {self.get_scientific_score()}/100)")
        print(f"   🎯 WMA周期: {self.wma_periods}")
        print(f"   📊 数据限制: 严格50行 (科学标准)")
        print(f"   📁 数据路径: {self.data_path}")
        
        # 🔬 科学建议
        self._provide_scientific_recommendation()
    
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
            'optimization': f'严格{self.required_rows}行数据限制 (科学标准)'
        } 