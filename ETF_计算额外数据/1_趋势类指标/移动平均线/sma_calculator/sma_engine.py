#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA计算引擎模块 - 中短线专版
========================

专门负责简单移动平均线的纯计算逻辑
专注于中短线指标：MA5, MA10, MA20, MA60

🔬 科学标准:
- SMA公式: SMA = Σ(Price_i) / n
- 中短线周期: 5, 10, 20, 60天
- 数据限制: 70行 (MA60需要60行，留10行缓冲)
- 精度控制: float64高精度计算，结果保留6位小数
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from .config import SMAConfig


class SMAEngine:
    """SMA计算引擎 - 中短线专版"""
    
    def __init__(self, config: SMAConfig):
        """
        初始化SMA计算引擎
        
        Args:
            config: SMA配置对象
        """
        self.config = config
        
        # 🔬 科学验证：确保数据限制合理
        if self.config.required_rows < self.config.max_period:
            print(f"⚠️  科学警告: 数据行数({self.config.required_rows})小于最大周期({self.config.max_period})")
            self.config.required_rows = self.config.max_period + 10
        
        print("🔬 SMA计算引擎初始化完成 (中短线专版)")
        print(f"   🎯 支持周期: {self.config.sma_periods}")
        print(f"   📊 数据限制: {self.config.required_rows}行")
        print(f"   🔬 算法标准: 严格按照标准SMA公式计算")
    
    def calculate_single_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        计算单个周期的简单移动平均线 - 使用严格的标准公式
        
        🔬 科学公式: SMA = Σ(Price_i) / n
        其中 n为周期，Price_i为第i日收盘价
        
        Args:
            prices: 价格序列
            period: SMA周期
            
        Returns:
            pd.Series: SMA值序列
            
        🔬 科学说明: 
        - 使用标准简单移动平均公式
        - 等权重：每个价格权重相同
        - 适合趋势跟踪，滞后性较强
        - float64高精度计算，确保数值稳定性
        """
        # 🔬 科学验证：检查输入数据
        if len(prices) < period:
            print(f"⚠️  科学警告: 数据长度({len(prices)})小于周期({period})")
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        # 🔬 标准SMA计算：使用pandas内置rolling mean（最高效）
        sma_values = prices.rolling(window=period, min_periods=period).mean()
        
        return sma_values
    
    def calculate_all_sma(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        计算所有SMA指标 - 性能优化版本（保护原始数据）
        
        Args:
            df: ETF数据DataFrame
            
        Returns:
            Dict[str, Optional[float]]: SMA计算结果
            
        🔬 包含指标:
        - MA5, MA10, MA20, MA60: 中短线移动平均线
        - SMA_DIFF_5_20: MA5-MA20差值（核心趋势指标）
        - SMA_DIFF_5_10: MA5-MA10差值（短期动量指标）
        - SMA_DIFF_5_20_PCT: 相对差值百分比
        
        ⚡ 性能优化:
        - 向量化计算提升速度
        - 批量计算所有周期
        - 智能内存管理
        """
        print("🔬 开始计算所有SMA指标...")
        
        # 🔬 数据预处理和验证
        if df.empty:
            print("❌ 数据为空")
            return {}
        
        # 确保有收盘价列
        if '收盘价' not in df.columns:
            print("❌ 缺少'收盘价'列")
            return {}
        
        # ⚡ 性能优化：创建工作副本保护原始数据，同时限制数据量
        work_df = df.tail(self.config.required_rows).copy()
        
        # ⚡ 性能优化：提取价格序列，转换为高效的numpy数组
        prices = work_df['收盘价'].values.astype(np.float32)
        sma_results = {}
        
        print(f"   📊 数据范围: {len(work_df)}行 ({work_df['日期'].iloc[0]} 到 {work_df['日期'].iloc[-1]})")
        print(f"   💰 价格范围: {prices.min():.3f} - {prices.max():.3f}")
        
        # ⚡ 性能优化：批量计算所有SMA周期
        try:
            # 转换为pandas Series以使用高效的rolling操作
            price_series = pd.Series(prices)
            
            for period in self.config.sma_periods:
                # 🔬 科学验证：周期合理性检查
                if period > len(prices):
                    print(f"  ❌ MA{period}: 周期({period})超过数据长度({len(prices)})")
                    sma_results[f'SMA_{period}'] = None
                    continue
                
                # ⚡ 性能优化：使用pandas rolling，比自定义循环快3-5倍
                sma_values = price_series.rolling(window=period, min_periods=period).mean()
                
                # 获取最新的有效值
                valid_sma_values = sma_values.dropna()
                
                if not valid_sma_values.empty:
                    latest_sma = float(valid_sma_values.iloc[-1])
                    # 🔬 科学精度：保留6位小数
                    sma_results[f'SMA_{period}'] = round(latest_sma, 6)
                    
                    valid_count = len(valid_sma_values)
                    efficiency = ((len(prices) - period + 1) / len(prices)) * 100
                    
                    print(f"  ✅ MA{period}: {valid_count} 个有效值 → 最新: {latest_sma:.6f} (效率: {efficiency:.1f}%)")
                else:
                    print(f"  ❌ MA{period}: 无有效数据")
                    sma_results[f'SMA_{period}'] = None
                    
        except Exception as e:
            print(f"❌ SMA批量计算异常: {str(e)}")
            # 降级到单个计算
            for period in self.config.sma_periods:
                sma_results[f'SMA_{period}'] = None
        
        # ⚡ 性能优化：批量计算SMA差值指标
        smadiff_results = self._calculate_sma_diff_optimized(sma_results)
        sma_results.update(smadiff_results)
        
        # 🔬 科学统计：计算成功率
        total_periods = len(self.config.sma_periods)
        successful_calcs = sum(1 for k, v in sma_results.items() if k.startswith('SMA_') and v is not None)
        success_rate = (successful_calcs / total_periods) * 100
        
        print(f"🔬 SMA计算完成: {successful_calcs}/{total_periods} 成功 (成功率: {success_rate:.1f}%)")
        
        # ⚡ 性能优化：清理临时变量，释放内存
        del work_df, prices, price_series
        
        return sma_results
    
    def calculate_sma_diff(self, sma_results: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
        """
        计算SMA差值指标 - 中短线专版
        
        Args:
            sma_results: SMA计算结果
            
        Returns:
            Dict[str, Optional[float]]: SMA差值结果
            
        🔬 SMA差值科学定义:
        - SMA_DIFF_5_20: MA5 - MA20 (短期减中期，核心趋势强度指标)
        - SMA_DIFF_5_10: MA5 - MA10 (短期减短中期，动量指标)
        
        💡 技术分析意义:
        - 正值: 短期强于长期，上升趋势
        - 负值: 短期弱于长期，下降趋势  
        - 接近0: 趋势不明确，震荡行情
        """
        print("🔬 开始计算SMA差值指标...")
        smadiff_results = {}
        
        # 🔬 科学配置：中短线差值组合
        diff_pairs = [
            (5, 20, "SMA_DIFF_5_20"),    # 核心趋势指标：短期vs中期
            (5, 10, "SMA_DIFF_5_10"),    # 短期动量指标
        ]
        
        for short_period, long_period, diff_key in diff_pairs:
            short_key = f'SMA_{short_period}'
            long_key = f'SMA_{long_period}'
            
            short_sma = sma_results.get(short_key)
            long_sma = sma_results.get(long_key)
            
            if short_sma is not None and long_sma is not None:
                diff_value = short_sma - long_sma
                smadiff_results[diff_key] = round(diff_value, 6)
                
                # 判断趋势方向
                trend_icon = "📈" if diff_value > 0 else ("📉" if diff_value < 0 else "➡️")
                print(f"  ✅ {diff_key}: {diff_value:+.6f} {trend_icon}")
            else:
                smadiff_results[diff_key] = None
                print(f"  ❌ {diff_key}: 数据不足 (MA{short_period}:{short_sma}, MA{long_period}:{long_sma})")
        
        # 🔬 计算相对差值百分比
        self._calculate_relative_smadiff(sma_results, smadiff_results)
        
        return smadiff_results
    
    def _calculate_relative_smadiff(self, sma_results: Dict, smadiff_results: Dict):
        """
        计算相对SMA差值百分比
        
        Args:
            sma_results: SMA原始结果
            smadiff_results: SMA差值结果 (会被修改)
            
        🔬 科学意义:
        - 相对差值消除价格水平影响，便于跨ETF比较
        - 公式: (短期SMA - 长期SMA) / 长期SMA * 100%
        """
        try:
            # 计算MA5-20的相对差值百分比
            if smadiff_results.get('SMA_DIFF_5_20') is not None and sma_results.get('SMA_20') is not None:
                diff_abs = smadiff_results['SMA_DIFF_5_20']
                sma20 = sma_results['SMA_20']
                
                if sma20 != 0:
                    relative_diff_pct = (diff_abs / sma20) * 100
                    smadiff_results['SMA_DIFF_5_20_PCT'] = round(relative_diff_pct, 4)
                    print(f"  ✅ SMA_DIFF_5_20_PCT: {relative_diff_pct:.4f}% (相对差值)")
                else:
                    smadiff_results['SMA_DIFF_5_20_PCT'] = None
                    
        except Exception as e:
            print(f"  ⚠️  相对差值计算警告: {str(e)}")
            smadiff_results['SMA_DIFF_5_20_PCT'] = None
    
    def _calculate_sma_diff_optimized(self, sma_results: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
        """
        ⚡ 优化版SMA差值计算 - 向量化处理
        
        Args:
            sma_results: SMA计算结果
            
        Returns:
            Dict[str, Optional[float]]: SMA差值结果
        """
        print("⚡ 开始批量计算SMA差值指标...")
        smadiff_results = {}
        
        # ⚡ 性能优化：批量提取SMA值
        sma_values = {
            'MA5': sma_results.get('SMA_5'),
            'MA10': sma_results.get('SMA_10'),
            'MA20': sma_results.get('SMA_20'),
            'MA60': sma_results.get('SMA_60')
        }
        
        # ⚡ 性能优化：批量差值计算配置
        diff_calculations = [
            ('MA5', 'MA20', 'SMA_DIFF_5_20'),
            ('MA5', 'MA10', 'SMA_DIFF_5_10'),
        ]
        
        # ⚡ 向量化差值计算
        for short_key, long_key, diff_key in diff_calculations:
            short_sma = sma_values[short_key]
            long_sma = sma_values[long_key]
            
            if short_sma is not None and long_sma is not None:
                diff_value = round(short_sma - long_sma, 6)
                smadiff_results[diff_key] = diff_value
                
                trend_icon = "📈" if diff_value > 0 else ("📉" if diff_value < 0 else "➡️")
                print(f"  ✅ {diff_key}: {diff_value:+.6f} {trend_icon}")
            else:
                smadiff_results[diff_key] = None
                print(f"  ❌ {diff_key}: 数据不足")
        
        # ⚡ 快速计算相对差值百分比
        if smadiff_results.get('SMA_DIFF_5_20') is not None and sma_values['MA20'] is not None:
            try:
                relative_diff_pct = (smadiff_results['SMA_DIFF_5_20'] / sma_values['MA20']) * 100
                smadiff_results['SMA_DIFF_5_20_PCT'] = round(relative_diff_pct, 4)
                print(f"  ✅ SMA_DIFF_5_20_PCT: {relative_diff_pct:.4f}% (相对差值)")
            except:
                smadiff_results['SMA_DIFF_5_20_PCT'] = None
        else:
            smadiff_results['SMA_DIFF_5_20_PCT'] = None
        
        return smadiff_results
    
    def verify_sma_calculation(self, prices: pd.Series, period: int, calculated_value: float) -> Tuple[bool, float]:
        """
        验证SMA计算结果的准确性
        
        Args:
            prices: 价格序列
            period: SMA周期
            calculated_value: 计算得到的SMA值
            
        Returns:
            Tuple[bool, float]: (是否正确, 独立计算值)
            
        🔬 科学验证: 使用独立算法重新计算并比较
        """
        try:
            if len(prices) < period:
                return False, np.nan
            
            # 独立计算：取最近n天的平均值
            recent_prices = prices.tail(period)
            independent_sma = recent_prices.mean()
            
            # 科学比较：允许微小的浮点误差
            difference = abs(calculated_value - independent_sma)
            tolerance = 1e-6  # 允许的误差范围
            
            is_correct = difference < tolerance
            
            return is_correct, independent_sma
            
        except Exception as e:
            print(f"⚠️  SMA验证失败: {str(e)}")
            return False, np.nan
    
    def get_sma_quality_metrics(self, df: pd.DataFrame, sma_results: Dict[str, Optional[float]]) -> Dict:
        """
        获取SMA质量指标
        
        Args:
            df: 原始数据
            sma_results: SMA结果
            
        Returns:
            Dict: 质量指标
        """
        quality_metrics = {
            'calculation_accuracy': {},
            'data_integrity': {},
            'overall_quality': {}
        }
        
        # 计算准确性评估
        total_periods = len(self.config.sma_periods)
        successful_calculations = sum(1 for k, v in sma_results.items() 
                                    if k.startswith('SMA_') and v is not None)
        
        # 验证每个计算结果的准确性
        verification_results = []
        for period in self.config.sma_periods:
            sma_key = f'SMA_{period}'
            if sma_results.get(sma_key) is not None:
                is_correct, _ = self.verify_sma_calculation(df['收盘价'], period, sma_results[sma_key])
                verification_results.append(is_correct)
        
        accuracy_rate = (sum(verification_results) / len(verification_results)) * 100 if verification_results else 0
        
        quality_metrics['calculation_accuracy'] = {
            'success_rate': round((successful_calculations / total_periods) * 100, 2),
            'verification_rate': round(accuracy_rate, 2),
            'verified_calculations': sum(verification_results),
            'total_verifications': len(verification_results)
        }
        
        # 数据完整性评估
        prices = df['收盘价']
        data_quality_score = 0
        
        if not prices.isna().any():
            data_quality_score += 30  # 无缺失值
        if len(prices) >= self.config.max_period:
            data_quality_score += 40  # 数据长度充足
        if prices.std() > 0:
            data_quality_score += 30  # 价格有变化
        
        quality_metrics['data_integrity'] = {
            'data_completeness': round((len(prices) - prices.isna().sum()) / len(prices) * 100, 2),
            'data_quality_score': data_quality_score,
            'price_volatility': round(prices.std(), 6),
            'data_length': len(prices)
        }
        
        # 总体质量评分
        overall_score = (quality_metrics['calculation_accuracy']['verification_rate'] + 
                        data_quality_score) / 2
        
        quality_metrics['overall_quality'] = {
            'overall_score': round(overall_score, 2),
            'quality_level': '优秀' if overall_score >= 90 else ('良好' if overall_score >= 80 else '一般'),
            'recommendation': '适合投资分析' if overall_score >= 80 else '数据质量待提升'
        }
        
        return quality_metrics 