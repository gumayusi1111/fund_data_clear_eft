#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA计算引擎模块 - 科学严谨版
==========================

专门负责加权移动平均线的纯计算逻辑
使用严格的数学公式，确保计算精度和科学性

🔬 科学标准:
- WMA公式: WMA = Σ(Price_i × Weight_i) / Σ(Weight_i)
- 权重序列: 1, 2, 3, ..., n (线性递增)
- 数据限制: 严格50行 (WMA20需要20行，留30行缓冲)
- 精度控制: float64高精度计算，结果保留6位小数
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from .config import WMAConfig


class WMAEngine:
    """WMA计算引擎 - 科学严谨版本"""
    
    def __init__(self, config: WMAConfig):
        """
        初始化WMA计算引擎
        
        Args:
            config: WMA配置对象
        """
        self.config = config
        
        # 🔬 科学验证：确保数据限制为50行
        if self.config.required_rows != 50:
            print(f"⚠️  科学警告: 数据行数应为50行，当前为{self.config.required_rows}行")
            self.config.required_rows = 50
        
        print("🔬 WMA计算引擎初始化完成 (科学严谨版)")
        print(f"   🎯 支持周期: {self.config.wma_periods}")
        print(f"   📊 数据限制: 严格50行 (WMA20需要20行，留30行缓冲)")
        print(f"   🔬 算法标准: 严格按照标准WMA公式计算")
    
    def calculate_single_wma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        计算单个周期的加权移动平均线 - 使用严格的标准公式
        
        🔬 科学公式: WMA = Σ(Price_i × Weight_i) / Σ(Weight_i)
        其中 Weight_i = i (i = 1, 2, ..., n)，最新价格权重最大
        
        Args:
            prices: 价格序列
            period: WMA周期
            
        Returns:
            pd.Series: WMA值序列
            
        🔬 科学说明: 
        - 使用标准线性加权移动平均公式
        - 权重递增：1, 2, 3, ..., n
        - 最新数据权重最高，符合技术分析理论
        - float64高精度计算，确保数值稳定性
        """
        # 🔬 科学验证：检查输入数据
        if len(prices) < period:
            print(f"⚠️  科学警告: 数据长度({len(prices)})小于周期({period})")
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        # 🔬 标准WMA权重计算：线性递增权重
        weights = np.arange(1, period + 1, dtype=np.float64)
        weights_sum = weights.sum()  # 权重总和
        
        def calculate_wma_point(price_window):
            """
            计算单个WMA点的严格算法
            
            🔬 科学公式: WMA = Σ(Price_i × i) / Σ(i), i=1,2,...,n
            """
            if len(price_window) < period:
                return np.nan
            
            # 确保数据类型为float64，提高计算精度
            price_array = np.array(price_window, dtype=np.float64)
            
            # 严格按照WMA公式计算
            weighted_sum = np.dot(price_array, weights)
            wma_value = weighted_sum / weights_sum
            
            return wma_value
        
        # 使用滑动窗口计算WMA - 不修改原始数据
        wma_values = prices.rolling(window=period, min_periods=period).apply(
            calculate_wma_point, raw=True
        )
        
        return wma_values
    
    def calculate_all_wma(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        计算所有周期的WMA指标 - 科学严谨版本
        
        Args:
            df: 包含价格数据的DataFrame (严格50行)
            
        Returns:
            Dict[str, Optional[float]]: WMA结果字典
            
        🔬 科学标准:
        - 严格验证数据完整性
        - 使用标准WMA公式
        - 结果精度控制到小数点后6位
        """
        print("🔬 开始科学WMA计算...")
        wma_results = {}
        
        # 🔬 科学验证：数据完整性检查
        if df.empty:
            print("❌ 科学错误: 输入数据为空")
            return wma_results
            
        if '收盘价' not in df.columns:
            print("❌ 科学错误: 缺少收盘价字段")
            return wma_results
        
        # 🔬 科学验证：数据行数检查 (应为50行)
        if len(df) != 50:
            print(f"⚠️  科学警告: 数据行数为{len(df)}行，期望50行")
            if len(df) < 20:
                print("❌ 科学错误: 数据不足，无法计算WMA20")
                return wma_results
        
        prices = df['收盘价'].copy()  # 创建副本，保护原数据
        
        # 🔬 科学验证：价格数据检查
        if prices.isnull().any():
            print(f"⚠️  科学警告: 检测到{prices.isnull().sum()}个缺失价格值")
            # 使用前向填充处理缺失值
            prices = prices.fillna(method='ffill')
        
        for period in self.config.wma_periods:
            try:
                # 🔬 科学验证：周期合理性检查
                if period > len(prices):
                    print(f"  ❌ WMA{period}: 周期({period})超过数据长度({len(prices)})")
                    wma_results[f'WMA_{period}'] = None
                    continue
                
                wma_values = self.calculate_single_wma(prices, period)
                
                # 获取最新的有效值，确保精度
                valid_wma_values = wma_values.dropna()
                
                if not valid_wma_values.empty:
                    latest_wma = valid_wma_values.iloc[-1]
                    # 🔬 科学精度：保留6位小数
                    latest_wma = round(float(latest_wma), 6)
                    wma_results[f'WMA_{period}'] = latest_wma
                    
                    valid_count = len(valid_wma_values)
                    efficiency = ((len(prices) - period + 1) / len(prices)) * 100
                    
                    print(f"  ✅ WMA{period}: {valid_count} 个有效值 → 最新: {latest_wma:.6f} (效率: {efficiency:.1f}%)")
                else:
                    print(f"  ❌ WMA{period}: 无有效数据")
                    wma_results[f'WMA_{period}'] = None
                    
            except Exception as e:
                print(f"  ❌ WMA{period} 计算异常: {str(e)}")
                wma_results[f'WMA_{period}'] = None
        
        # 🔬 科学统计：计算成功率
        total_periods = len(self.config.wma_periods)
        successful_calcs = sum(1 for v in wma_results.values() if v is not None)
        success_rate = (successful_calcs / total_periods) * 100
        
        print(f"🔬 WMA计算完成: {successful_calcs}/{total_periods} 成功 (成功率: {success_rate:.1f}%)")
        
        return wma_results
    
    def verify_wma_calculation(self, prices: pd.Series, period: int, expected_wma: float) -> Tuple[bool, float]:
        """
        验证WMA计算的正确性 - 使用独立算法
        
        Args:
            prices: 价格序列
            period: WMA周期
            expected_wma: 期望的WMA值
            
        Returns:
            Tuple[bool, float]: (是否正确, 实际计算值)
            
        🔬 科学验证：使用完全独立的算法重新计算，确保结果准确性
        """
        if len(prices) < period:
            return False, np.nan
        
        # 获取最近period个价格
        recent_prices = prices.tail(period).values
        
        # 🔬 独立算法：手工计算WMA
        weights = np.arange(1, period + 1, dtype=np.float64)
        weighted_sum = np.sum(recent_prices * weights)
        weights_sum = np.sum(weights)
        independent_wma = weighted_sum / weights_sum
        
        # 精度比较（允许小的浮点数误差）
        tolerance = 1e-6
        is_correct = abs(independent_wma - expected_wma) < tolerance
        
        return is_correct, round(independent_wma, 6)
    
    def calculate_wma_statistics(self, df: pd.DataFrame, wma_results: Dict[str, Optional[float]]) -> Dict:
        """
        计算WMA统计信息 - 科学严谨版本
        
        Args:
            df: 原始数据
            wma_results: WMA计算结果
            
        Returns:
            Dict: 统计信息
            
        🔬 科学统计: 包含计算验证、趋势分析、收敛性分析
        """
        stats = {
            'calculation_verification': {},  # 计算验证
            'trend_analysis': {},           # 趋势分析
            'convergence_analysis': {},     # 收敛性分析
            'efficiency_metrics': {}       # 效率指标
        }
        
        prices = df['收盘价']
        
        for period in self.config.wma_periods:
            wma_key = f'WMA_{period}'
            
            if wma_results.get(wma_key) is not None:
                wma_value = wma_results[wma_key]
                
                # 🔬 计算验证：使用独立算法验证
                is_correct, independent_value = self.verify_wma_calculation(prices, period, wma_value)
                stats['calculation_verification'][f'WMA{period}'] = {
                    'is_correct': is_correct,
                    'calculated_value': wma_value,
                    'independent_value': independent_value,
                    'difference': round(abs(wma_value - independent_value), 8)
                }
                
                # 🔬 效率指标：计算数据利用率
                wma_values = self.calculate_single_wma(prices, period)
                valid_count = wma_values.count()
                total_possible = len(prices) - period + 1
                efficiency = (valid_count / len(prices)) * 100
                
                stats['efficiency_metrics'][f'WMA{period}'] = {
                    'valid_points': valid_count,
                    'total_possible': total_possible,
                    'data_efficiency': round(efficiency, 2),
                    'utilization_rate': round((valid_count / total_possible) * 100, 2) if total_possible > 0 else 0
                }
                
                # 🔬 趋势分析：科学的趋势强度计算
                recent_wma = wma_values.tail(min(10, valid_count)).dropna()  # 最近10个有效值
                if len(recent_wma) >= 3:
                    # 线性回归计算趋势强度
                    x = np.arange(len(recent_wma))
                    y = recent_wma.values
                    
                    # 计算斜率（趋势方向和强度）
                    slope = np.polyfit(x, y, 1)[0]
                    trend_strength = abs(slope / wma_value) * 100 if wma_value != 0 else 0
                    
                    # 计算相关系数（趋势一致性）
                    correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
                    
                    stats['trend_analysis'][f'WMA{period}'] = {
                        'slope': round(slope, 8),
                        'trend_strength_pct': round(trend_strength, 4),
                        'trend_consistency': round(correlation, 4),
                        'direction': '上升' if slope > 0 else ('下降' if slope < 0 else '平稳'),
                        'recent_change': round(recent_wma.iloc[-1] - recent_wma.iloc[0], 6),
                        'recent_change_pct': round(((recent_wma.iloc[-1] / recent_wma.iloc[0]) - 1) * 100, 4)
                    }
                
                # 🔬 收敛性分析：WMA与价格的关系
                current_price = prices.iloc[-1]
                price_wma_diff = current_price - wma_value
                price_wma_ratio = (price_wma_diff / current_price) * 100 if current_price != 0 else 0
                
                stats['convergence_analysis'][f'WMA{period}'] = {
                    'current_price': round(current_price, 6),
                    'wma_value': wma_value,
                    'absolute_difference': round(price_wma_diff, 6),
                    'relative_difference_pct': round(price_wma_ratio, 4),
                    'position': '价格在WMA上方' if price_wma_diff > 0 else ('价格在WMA下方' if price_wma_diff < 0 else '价格与WMA重合')
                }
        
        return stats
    
    def get_wma_quality_metrics(self, df: pd.DataFrame, wma_results: Dict[str, Optional[float]]) -> Dict:
        """
        获取WMA质量指标 - 科学严谨版本
        
        Args:
            df: 原始数据
            wma_results: WMA结果
            
        Returns:
            Dict: 质量指标
            
        🔬 科学质量评估: 包含计算准确性、数据完整性、算法可靠性
        """
        quality_metrics = {
            'calculation_accuracy': {},    # 计算准确性
            'data_integrity': {},         # 数据完整性
            'algorithm_reliability': {},  # 算法可靠性
            'overall_quality': {}         # 总体质量
        }
        
        # 🔬 计算准确性评估
        total_periods = len(self.config.wma_periods)
        successful_calculations = sum(1 for v in wma_results.values() if v is not None)
        
        # 验证每个计算结果的准确性
        verification_results = []
        for period in self.config.wma_periods:
            wma_key = f'WMA_{period}'
            if wma_results.get(wma_key) is not None:
                is_correct, _ = self.verify_wma_calculation(df['收盘价'], period, wma_results[wma_key])
                verification_results.append(is_correct)
        
        accuracy_rate = (sum(verification_results) / len(verification_results)) * 100 if verification_results else 0
        
        quality_metrics['calculation_accuracy'] = {
            'success_rate': round((successful_calculations / total_periods) * 100, 2),
            'verification_rate': round(accuracy_rate, 2),
            'verified_calculations': sum(verification_results),
            'total_verifications': len(verification_results)
        }
        
        # 🔬 数据完整性评估
        prices = df['收盘价']
        data_quality_score = 0
        
        if not df.empty:
            # 基础完整性
            completeness = (prices.count() / len(df)) * 100
            
            # 数据一致性（无异常值）
            if prices.count() > 1:
                price_std = prices.std()
                price_mean = prices.mean()
                cv = (price_std / price_mean) * 100 if price_mean != 0 else 0  # 变异系数
                consistency_score = max(0, 100 - min(cv, 100))  # CV越小，一致性越好
            else:
                consistency_score = 0
            
            # 数据连续性（无大幅跳跃）
            if len(prices) > 1:
                price_changes = prices.pct_change().dropna()
                extreme_changes = (abs(price_changes) > 0.15).sum()  # 15%以上变化视为异常
                continuity_score = max(0, 100 - (extreme_changes / len(price_changes)) * 100)
            else:
                continuity_score = 0
            
            data_quality_score = (completeness + consistency_score + continuity_score) / 3
        
        quality_metrics['data_integrity'] = {
            'completeness_pct': round(completeness, 2) if not df.empty else 0,
            'consistency_score': round(consistency_score, 2) if not df.empty else 0,
            'continuity_score': round(continuity_score, 2) if not df.empty else 0,
            'overall_data_quality': round(data_quality_score, 2)
        }
        
        # 🔬 算法可靠性评估
        if successful_calculations >= 2:
            wma_values_list = [v for v in wma_results.values() if v is not None]
            
            # WMA序列的合理性（短周期WMA应更贴近价格）
            current_price = prices.iloc[-1] if not df.empty else 0
            wma_deviations = []
            
            for period in self.config.wma_periods:
                wma_key = f'WMA_{period}'
                if wma_results.get(wma_key) is not None:
                    deviation = abs(wma_results[wma_key] - current_price) / current_price * 100 if current_price != 0 else 0
                    wma_deviations.append((period, deviation))
            
            # 检查是否符合预期：短周期偏差更小
            ordered_deviations = sorted(wma_deviations, key=lambda x: x[0])  # 按周期排序
            monotonicity_score = 100  # 单调性评分
            
            for i in range(len(ordered_deviations) - 1):
                if ordered_deviations[i][1] > ordered_deviations[i+1][1]:  # 短周期偏差应该更小
                    monotonicity_score -= 20
            
            monotonicity_score = max(0, monotonicity_score)
            
            # WMA值的平滑性
            if len(wma_values_list) >= 2:
                max_wma = max(wma_values_list)
                min_wma = min(wma_values_list)
                relative_range = ((max_wma - min_wma) / max_wma) * 100 if max_wma > 0 else 0
                smoothness_score = max(0, 100 - relative_range)
            else:
                smoothness_score = 0
            
        else:
            monotonicity_score = 0
            smoothness_score = 0
        
        quality_metrics['algorithm_reliability'] = {
            'monotonicity_score': round(monotonicity_score, 2),
            'smoothness_score': round(smoothness_score, 2),
            'wma_deviations': {f'WMA{d[0]}': round(d[1], 4) for d in (wma_deviations if 'wma_deviations' in locals() else [])}
        }
        
        # 🔬 总体质量评分
        overall_score = (
            quality_metrics['calculation_accuracy']['verification_rate'] * 0.4 +
            quality_metrics['data_integrity']['overall_data_quality'] * 0.3 +
            quality_metrics['algorithm_reliability']['monotonicity_score'] * 0.15 +
            quality_metrics['algorithm_reliability']['smoothness_score'] * 0.15
        )
        
        quality_level = '优秀' if overall_score >= 90 else ('良好' if overall_score >= 75 else ('一般' if overall_score >= 60 else '需改进'))
        
        quality_metrics['overall_quality'] = {
            'total_score': round(overall_score, 2),
            'quality_level': quality_level,
            'recommendation': self._get_quality_recommendation(overall_score)
        }
        
        return quality_metrics
    
    def _get_quality_recommendation(self, score: float) -> str:
        """根据质量评分提供建议"""
        if score >= 90:
            return "WMA计算质量优秀，可以放心使用"
        elif score >= 75:
            return "WMA计算质量良好，建议监控数据完整性"
        elif score >= 60:
            return "WMA计算质量一般，建议检查数据质量和增加数据量"
        else:
            return "WMA计算质量较差，建议检查数据源和算法实现" 