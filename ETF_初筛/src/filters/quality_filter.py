#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格质量筛选器
实现request.md中定义的价格质量检查和数据质量验证逻辑
严格基于11个基础字段
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from .base_filter import BaseFilter, FilterResult


class QualityFilter(BaseFilter):
    """价格质量筛选器 - 基于request.md设计"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("价格质量筛选器", config)
        
        # 从配置获取参数
        价格质量配置 = self.config.get("价格质量标准", {})
        数据质量配置 = self.config.get("数据质量要求", {})
        异常波动配置 = self.config.get("异常波动阈值", {})
        筛选配置 = self.config.get("筛选配置", {})
        
        self.观察期天数 = 筛选配置.get("观察期_天数", 30)
        self.容错比例 = 筛选配置.get("容错比例", 0.1)
        
        # 价格质量标准
        self.最低价格 = 价格质量配置.get("最低价格", 0.01)
        self.最高价格 = 价格质量配置.get("最高价格", 500)
        self.跳空阈值 = 价格质量配置.get("跳空阈值", 0.20)
        self.价格变化率阈值 = 价格质量配置.get("价格变化率阈值", 0.001)
        self.连续相同价格限制 = 价格质量配置.get("连续相同价格限制", 3)
        self.活跃天数要求 = 价格质量配置.get("活跃天数要求", 5)
        
        # 数据质量要求
        self.缺失率上限 = 数据质量配置.get("缺失率上限", 0.05)
        逻辑检查误差 = 数据质量配置.get("逻辑检查误差", {})
        self.涨跌误差 = 逻辑检查误差.get("涨跌误差", 0.01)
        self.涨幅误差 = 逻辑检查误差.get("涨幅误差", 0.001)
        
        # 细化容错率：OHLC vs 成交数据
        self.ohlc容错率 = 0.10  # OHLC数据容错10%
        self.成交数据容错率 = 0.05  # 成交额/量容错5%
        
        # 异常波动设置
        self.普通ETF阈值 = 异常波动配置.get("普通ETF", 0.10)
        self.异常天数限制 = 异常波动配置.get("异常天数限制", 2)
        self.异常振幅阈值 = 异常波动配置.get("异常振幅阈值", 0.15)
    
    def filter_single_etf(self, etf_code: str, df: pd.DataFrame) -> FilterResult:
        """筛选单个ETF的价格质量"""
        
        # 数据有效性检查
        if not self.is_valid_data(df, self.观察期天数):
            return FilterResult(
                etf_code=etf_code,
                passed=False,
                score=0.0,
                reason=f"数据不足{self.观察期天数}天",
                metrics={}
            )
        
        # 计算质量指标
        质量指标 = self._calculate_quality_metrics(df)
        
        # 执行质量检查
        检查结果, 原因 = self._check_quality_requirements(质量指标)
        
        return FilterResult(
            etf_code=etf_code,
            passed=检查结果,
            score=100.0 if 检查结果 else 0.0,
            reason=原因,
            metrics=质量指标
        )
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算价格质量指标"""
        try:
            metrics = {}
            
            # 取最近观察期的数据
            recent_df = df.tail(self.观察期天数).copy()
            
            # 1. 数据完整性检查
            必要字段 = ['代码', '日期', '开盘价', '最高价', '最低价', '收盘价', '成交量(手数)', '成交额(千元)']
            可用字段 = [col for col in 必要字段 if col in recent_df.columns]
            
            总数据点 = len(recent_df) * len(可用字段)
            缺失数据点 = recent_df[可用字段].isna().sum().sum()
            缺失率 = 缺失数据点 / 总数据点 if 总数据点 > 0 else 1.0
            metrics["数据缺失率"] = 缺失率
            
            # 2. OHLC逻辑检查
            ohlc_字段 = ['开盘价', '最高价', '最低价', '收盘价', '上日收盘']
            if all(col in recent_df.columns for col in ohlc_字段):
                ohlc_错误 = self._check_ohlc_logic(recent_df)
                metrics["OHLC逻辑错误数"] = ohlc_错误
                metrics["OHLC逻辑错误率"] = ohlc_错误 / len(recent_df)
            
            # 3. 价格合理性检查
            if '收盘价' in recent_df.columns:
                收盘价 = recent_df['收盘价']
                metrics["最低收盘价"] = 收盘价.min()
                metrics["最高收盘价"] = 收盘价.max()
                metrics["价格范围合理"] = (收盘价.min() >= self.最低价格) and (收盘价.max() <= self.最高价格)
            
            # 4. 价格活跃度检查（最近10天）
            if '收盘价' in recent_df.columns and len(recent_df) >= 10:
                最近10天价格 = recent_df['收盘价'].tail(10)
                价格变化率 = 最近10天价格.std() / 最近10天价格.mean() if 最近10天价格.mean() > 0 else 0
                metrics["价格变化率"] = 价格变化率
                
                # 统计有价格变化的天数（优化：更精确的变动检测）
                价格变化天数 = (最近10天价格.diff().abs() > 0.001).sum()
                metrics["价格变化天数"] = 价格变化天数
                
                # 新增：价格变动次数检查（防止僵尸ETF）
                有效变动次数 = 0
                for i in range(1, len(最近10天价格)):
                    if abs(最近10天价格.iloc[i] - 最近10天价格.iloc[i-1]) > 0.001:
                        有效变动次数 += 1
                metrics["有效变动次数"] = 有效变动次数
                
                # 连续相同价格检查
                连续相同价格天数 = self._get_max_consecutive_same_price(最近10天价格)
                metrics["连续相同价格天数"] = 连续相同价格天数
            
            # 5. 异常波动检查
            if '涨幅%' in recent_df.columns:
                涨跌幅 = recent_df['涨幅%']
                异常波动天数 = (abs(涨跌幅) > self.普通ETF阈值 * 100).sum()
                metrics["异常波动天数"] = 异常波动天数
                metrics["异常波动比例"] = 异常波动天数 / len(recent_df)
            
            # 6. 振幅异常检查
            if all(col in recent_df.columns for col in ['最高价', '最低价', '上日收盘']):
                异常振幅天数 = self._check_amplitude_anomaly(recent_df)
                metrics["异常振幅天数"] = 异常振幅天数
                metrics["异常振幅比例"] = 异常振幅天数 / len(recent_df)
            
            # 7. 数据逻辑一致性检查
            if all(col in recent_df.columns for col in ['涨跌', '涨幅%', '收盘价', '上日收盘']):
                逻辑不一致数 = self._check_data_consistency(recent_df)
                metrics["逻辑不一致数"] = 逻辑不一致数
                metrics["逻辑不一致率"] = 逻辑不一致数 / len(recent_df)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"计算价格质量指标失败: {e}")
            return {}
    
    def _check_ohlc_logic(self, df: pd.DataFrame) -> int:
        """检查OHLC逻辑错误数"""
        错误数 = 0
        
        for _, row in df.iterrows():
            开盘 = row['开盘价']
            最高 = row['最高价'] 
            最低 = row['最低价']
            收盘 = row['收盘价']
            上日收盘 = row['上日收盘']
            
            # 基础OHLC逻辑检查
            if not (最低 <= 开盘 <= 最高 and 最低 <= 收盘 <= 最高 and 最低 <= 最高):
                错误数 += 1
                continue
            
            # 跳空检查
            if 上日收盘 > 0:
                跳空幅度 = abs(开盘 - 上日收盘) / 上日收盘
                if 跳空幅度 > self.跳空阈值:
                    # 这不算错误，但需要标记
                    pass
        
        return 错误数
    
    def _get_max_consecutive_same_price(self, prices: pd.Series) -> int:
        """计算最大连续相同价格天数"""
        if prices.empty:
            return 0
        
        最大连续 = 0
        当前连续 = 1
        
        for i in range(1, len(prices)):
            if abs(prices.iloc[i] - prices.iloc[i-1]) < 0.001:  # 价格基本相同
                当前连续 += 1
                最大连续 = max(最大连续, 当前连续)
            else:
                当前连续 = 1
        
        return 最大连续
    
    def _check_amplitude_anomaly(self, df: pd.DataFrame) -> int:
        """检查振幅异常天数"""
        异常天数 = 0
        
        for _, row in df.iterrows():
            最高价 = row['最高价']
            最低价 = row['最低价'] 
            上日收盘 = row['上日收盘']
            
            if 上日收盘 > 0:
                振幅 = (最高价 - 最低价) / 上日收盘
                if 振幅 > self.异常振幅阈值:
                    异常天数 += 1
        
        return 异常天数
    
    def _check_data_consistency(self, df: pd.DataFrame) -> int:
        """检查数据逻辑一致性（优化：细化容错率）"""
        不一致数 = 0
        
        for _, row in df.iterrows():
            涨跌 = row['涨跌']
            涨幅 = row['涨幅%']
            收盘价 = row['收盘价']
            上日收盘 = row['上日收盘']
            
            if 上日收盘 > 0:
                # 检查涨跌计算（价格数据用OHLC容错率10%）
                理论涨跌 = 收盘价 - 上日收盘
                相对误差 = abs(涨跌 - 理论涨跌) / max(abs(理论涨跌), 0.01)
                if 相对误差 > self.ohlc容错率:
                    不一致数 += 1
                    continue
                
                # 检查涨幅计算（价格数据用OHLC容错率10%）
                理论涨幅 = (收盘价 - 上日收盘) / 上日收盘 * 100
                if abs(涨幅 - 理论涨幅) > abs(理论涨幅) * self.ohlc容错率:
                    不一致数 += 1
        
        return 不一致数
    
    def _check_quality_requirements(self, metrics: Dict[str, Any]) -> Tuple[bool, str]:
        """检查质量要求"""
        问题列表 = []
        
        # 1. 数据完整性检查
        数据缺失率 = metrics.get("数据缺失率", 1.0)
        if 数据缺失率 > self.缺失率上限:
            问题列表.append(f"数据缺失率过高({数据缺失率:.1%}>{self.缺失率上限:.1%})")
        
        # 2. OHLC逻辑检查
        ohlc逻辑错误率 = metrics.get("OHLC逻辑错误率", 1.0)
        if ohlc逻辑错误率 > self.容错比例:
            问题列表.append(f"OHLC逻辑错误过多({ohlc逻辑错误率:.1%}>{self.容错比例:.1%})")
        
        # 3. 价格合理性检查
        价格范围合理 = metrics.get("价格范围合理", False)
        if not 价格范围合理:
            最低价 = metrics.get("最低收盘价", 0)
            最高价 = metrics.get("最高收盘价", 0)
            问题列表.append(f"价格范围异常(最低{最低价:.2f}元,最高{最高价:.2f}元)")
        
        # 4. 价格活跃度检查（优化：增加变动次数检查）
        价格变化率 = metrics.get("价格变化率", 0)
        if 价格变化率 < self.价格变化率阈值:
            问题列表.append(f"价格缺乏活跃度(变化率{价格变化率:.3f}<{self.价格变化率阈值:.3f})")
        
        价格变化天数 = metrics.get("价格变化天数", 0)
        if 价格变化天数 < self.活跃天数要求:
            问题列表.append(f"价格变化天数不足({价格变化天数}<{self.活跃天数要求}天)")
        
        # 新增：有效变动次数检查（防止僵尸ETF）
        有效变动次数 = metrics.get("有效变动次数", 0)
        if 有效变动次数 < 3:  # 最近10天至少变动3次
            问题列表.append(f"价格变动次数不足({有效变动次数}<3次，疑似僵尸ETF)")
        
        连续相同价格天数 = metrics.get("连续相同价格天数", 0)
        if 连续相同价格天数 > self.连续相同价格限制:
            问题列表.append(f"连续相同价格时间过长({连续相同价格天数}>{self.连续相同价格限制}天)")
        
        # 5. 异常波动检查
        异常波动天数 = metrics.get("异常波动天数", 999)
        if 异常波动天数 > self.异常天数限制:
            问题列表.append(f"异常波动天数过多({异常波动天数}>{self.异常天数限制}天)")
        
        异常振幅天数 = metrics.get("异常振幅天数", 999)
        if 异常振幅天数 > self.异常天数限制:
            问题列表.append(f"异常振幅天数过多({异常振幅天数}>{self.异常天数限制}天)")
        
        # 6. 数据逻辑一致性检查
        逻辑不一致率 = metrics.get("逻辑不一致率", 1.0)
        if 逻辑不一致率 > self.容错比例:
            问题列表.append(f"数据逻辑错误过多({逻辑不一致率:.1%}>{self.容错比例:.1%})")
        
        # 综合判断
        if len(问题列表) == 0:
            return True, "价格质量检查通过"
        else:
            return False, "; ".join(问题列表)
    
    def get_filter_description(self) -> Dict[str, Any]:
        """获取筛选器说明"""
        return {
            "筛选器名称": self.name,
            "设计依据": "request.md - 价格质量检查和数据质量验证 (已优化)",
            "检查项目": {
                "数据完整性": f"缺失率≤{self.缺失率上限:.1%}",
                "OHLC逻辑": f"错误率≤{self.容错比例:.1%}",
                "价格合理性": f"{self.最低价格}-{self.最高价格}元",
                "价格活跃度": f"变化率≥{self.价格变化率阈值:.3f}",
                "变动次数检查": "10天≥3次变动(防僵尸ETF)",
                "异常波动": f"≤{self.异常天数限制}天",
                "数据一致性": f"OHLC容错{self.ohlc容错率:.0%}/成交容错{self.成交数据容错率:.0%}"
            },
            "使用字段": [
                "开盘价", "最高价", "最低价", "收盘价", "上日收盘", 
                "涨跌", "涨幅%", "成交量(手数)", "成交额(千元)"
            ],
            "判断逻辑": "多维度检查，细化容错率，强化活跃度检测"
        } 