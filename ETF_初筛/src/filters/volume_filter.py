#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流动性门槛筛选器
实现request.md中定义的流动性门槛筛选逻辑
严格基于11个基础字段
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from .base_filter import BaseFilter, FilterResult


class VolumeFilter(BaseFilter):
    """流动性门槛筛选器 - 基于request.md设计"""
    
    def __init__(self, config: Dict[str, Any] = None, threshold_name: str = "5000万门槛"):
        super().__init__(f"流动性门槛筛选器({threshold_name})", config)
        
        self.threshold_name = threshold_name
        
        # 从配置获取参数
        流动性配置 = self.config.get("流动性门槛", {})
        筛选配置 = self.config.get("筛选配置", {})
        
        # 获取指定门槛的配置
        threshold_config = 流动性配置.get(threshold_name, {})
        
        # 如果找不到指定门槛配置，使用默认配置（兼容旧格式）
        if not threshold_config:
            if "日均成交额基准_万元" in 流动性配置:
                threshold_config = 流动性配置
            else:
                threshold_config = 流动性配置.get("5000万门槛", {})
        
        self.观察期天数 = 筛选配置.get("观察期_天数", 30)
        self.日均成交额基准 = threshold_config.get("日均成交额基准_万元", 5000) * 10  # 转为千元
        self.零成交量天数限制 = threshold_config.get("零成交量天数限制", 3)
        self.连续零成交天数限制 = threshold_config.get("连续零成交天数限制", 2)
        self.虚假流动性倍数 = threshold_config.get("虚假流动性倍数", 5)
        self.成交价格匹配误差 = threshold_config.get("成交价格匹配误差", 0.05)
        self.动态阈值分位数 = threshold_config.get("动态阈值_分位数", 0.3)
    
    def filter_single_etf(self, etf_code: str, df: pd.DataFrame) -> FilterResult:
        """筛选单个ETF的流动性"""
        
        # 数据有效性检查
        if not self.is_valid_data(df, self.观察期天数):
            return FilterResult(
                etf_code=etf_code,
                passed=False,
                score=0.0,
                reason=f"数据不足{self.观察期天数}天",
                metrics={}
            )
        
        # 计算流动性指标
        流动性指标 = self._calculate_liquidity_metrics(df)
        
        # 执行流动性检查
        检查结果, 原因 = self._check_liquidity_requirements(流动性指标)
        
        return FilterResult(
            etf_code=etf_code,
            passed=检查结果,
            score=100.0 if 检查结果 else 0.0,
            reason=原因,
            metrics=流动性指标
        )
    
    def _calculate_liquidity_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算流动性指标"""
        try:
            metrics = {}
            
            # 取最近观察期的数据
            recent_df = df.tail(self.观察期天数).copy()
            
            # 1. 基础流动性指标
            成交额 = recent_df['成交额(千元)'] if '成交额(千元)' in recent_df.columns else pd.Series()
            成交量 = recent_df['成交量(手数)'] if '成交量(手数)' in recent_df.columns else pd.Series()
            
            if not 成交额.empty:
                metrics["日均成交额"] = 成交额.mean()
                metrics["单日最大成交额"] = 成交额.max()
                
                # 零成交量统计
                零成交天数 = (成交量 == 0).sum() if not 成交量.empty else 0
                metrics["零成交量天数"] = 零成交天数
                
                # 连续零成交量统计
                连续零成交天数 = self._get_max_consecutive_zero_volume(成交量)
                metrics["连续零成交天数"] = 连续零成交天数
                
                # 成交量对应的平均价格
                if not 成交量.empty and '收盘价' in recent_df.columns:
                    收盘价 = recent_df['收盘价']
                    有效数据 = (成交量 > 0) & (成交额 > 0) & (收盘价 > 0)
                    
                    if 有效数据.any():
                        # 计算成交价格匹配性
                        成交价格 = (成交额 * 1000) / (成交量 * 100)  # 千元转元，手数转股数
                        价格差异 = abs(成交价格[有效数据] - 收盘价[有效数据]) / 收盘价[有效数据]
                        metrics["平均价格匹配误差"] = 价格差异.mean()
                        metrics["最大价格匹配误差"] = 价格差异.max()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"计算流动性指标失败: {e}")
            return {}
    
    def _get_max_consecutive_zero_volume(self, 成交量: pd.Series) -> int:
        """计算最大连续零成交量天数"""
        if 成交量.empty:
            return 0
        
        最大连续 = 0
        当前连续 = 0
        
        for volume in 成交量:
            if volume == 0:
                当前连续 += 1
                最大连续 = max(最大连续, 当前连续)
            else:
                当前连续 = 0
        
        return 最大连续
    
    def _check_liquidity_requirements(self, metrics: Dict[str, Any]) -> Tuple[bool, str]:
        """检查流动性要求"""
        问题列表 = []
        
        # 1. 日均成交额基础要求
        日均成交额 = metrics.get("日均成交额", 0)
        if 日均成交额 < self.日均成交额基准:
            问题列表.append(f"日均成交额不足({日均成交额:.0f}千元<{self.日均成交额基准}千元)")
        
        # 2. 零成交量天数检查
        零成交量天数 = metrics.get("零成交量天数", 999)
        if 零成交量天数 > self.零成交量天数限制:
            问题列表.append(f"零成交量天数过多({零成交量天数}>{self.零成交量天数限制}天)")
        
        # 3. 连续零成交量检查
        连续零成交天数 = metrics.get("连续零成交天数", 999)
        if 连续零成交天数 > self.连续零成交天数限制:
            问题列表.append(f"连续零成交量天数过多({连续零成交天数}>{self.连续零成交天数限制}天)")
        
        # 4. 虚假流动性检测
        单日最大成交额 = metrics.get("单日最大成交额", 0)
        if 日均成交额 > 0 and 单日最大成交额 > 日均成交额 * self.虚假流动性倍数:
            问题列表.append(f"可能存在虚假流动性(单日最大{单日最大成交额:.0f}千元 > 日均{日均成交额:.0f}千元×{self.虚假流动性倍数})")
        
        # 5. 成交价格匹配性检查
        平均价格匹配误差 = metrics.get("平均价格匹配误差", 0)
        if 平均价格匹配误差 > self.成交价格匹配误差:
            问题列表.append(f"成交价格匹配异常(误差{平均价格匹配误差:.1%}>{self.成交价格匹配误差:.1%})")
        
        # 综合判断
        if len(问题列表) == 0:
            return True, "流动性门槛检查通过"
        else:
            return False, "; ".join(问题列表)
    
    def get_filter_description(self) -> Dict[str, Any]:
        """获取筛选器说明"""
        return {
            "筛选器名称": self.name,
            "设计依据": "request.md - 流动性门槛筛选",
            "检查项目": {
                "日均成交额基准": f"{self.日均成交额基准}千元",
                "零成交量天数限制": f"≤{self.零成交量天数限制}天",
                "连续零成交天数限制": f"≤{self.连续零成交天数限制}天",
                "虚假流动性检测": f"单日峰值≤日均×{self.虚假流动性倍数}",
                "成交价格匹配": f"误差≤{self.成交价格匹配误差:.1%}"
            },
            "使用字段": ["成交额(千元)", "成交量(手数)", "收盘价"],
            "判断逻辑": "硬性门槛，任一项不满足即剔除"
        } 