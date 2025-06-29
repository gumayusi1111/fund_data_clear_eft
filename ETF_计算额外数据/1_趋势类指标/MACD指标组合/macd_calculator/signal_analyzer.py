#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD信号分析器
==============

专业的MACD技术信号分析模块
🎯 核心功能: 金叉死叉识别、零轴分析、信号强度评估
📊 分析维度: DIF/DEA交叉、零轴位置、柱状图变化、背离检测

"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from .config import MACDConfig
from .macd_engine import MACDEngine


class MACDSignalAnalyzer:
    """MACD信号分析器 - 专业技术分析版"""
    
    def __init__(self, config: MACDConfig):
        """
        初始化信号分析器
        
        Args:
            config: MACD配置对象
        """
        self.config = config
        self.macd_engine = MACDEngine(config)
        
        # 获取配置参数
        self.thresholds = config.get_signal_thresholds()
        self.weights = config.get_signal_weights()
        
        print("🎯 MACD信号分析器初始化完成")
        print(f"⚙️ 信号阈值: {self.thresholds}")
    
    def analyze_single_signal(self, current_price: float, historical_prices: List[float],
                             volumes: Optional[List[float]] = None) -> Dict:
        """
        分析单个时间点的MACD信号
        
        Args:
            current_price: 当前价格
            historical_prices: 历史价格序列
            volumes: 成交量序列（可选，用于背离分析）
            
        Returns:
            完整的MACD信号分析结果
        """
        # 确保有足够的历史数据
        min_required = self.macd_engine.slow_period + self.macd_engine.signal_period + 10
        if len(historical_prices) < min_required:
            return self._empty_signal_result("历史数据不足")
        
        # 计算MACD组件
        all_prices = historical_prices + [current_price]
        price_series = pd.Series(all_prices)
        components = self.macd_engine.calculate_macd_components(price_series)
        
        # 获取当前和前一个值
        current_dif = components['DIF'].iloc[-1]
        current_dea = components['DEA'].iloc[-1]
        current_macd = components['MACD'].iloc[-1]
        
        prev_dif = components['DIF'].iloc[-2] if len(components['DIF']) > 1 else None
        prev_dea = components['DEA'].iloc[-2] if len(components['DEA']) > 1 else None
        prev_macd = components['MACD'].iloc[-2] if len(components['MACD']) > 1 else None
        
        # 核心信号分析
        signal_analysis = {
            # 基础数值
            'current_dif': current_dif,
            'current_dea': current_dea,
            'current_macd': current_macd,
            'current_price': current_price,
            
            # 位置分析
            'dif_above_dea': current_dif > current_dea,
            'dif_above_zero': current_dif > 0,
            'dea_above_zero': current_dea > 0,
            'macd_above_zero': current_macd > 0,
            
            # 交叉信号分析
            **self._analyze_crossover_signals(current_dif, current_dea, prev_dif, prev_dea),
            
            # 强度分析
            **self._analyze_signal_strength(current_dif, current_dea, current_macd),
            
            # 趋势分析
            **self._analyze_trend_status(components['DIF'], components['DEA'], components['MACD']),
            
            # 综合评分
            'signal_score': 0.0,
            'signal_description': '',
            'trade_suggestion': '',
            'confidence_level': ''
        }
        
        # 计算综合评分
        signal_analysis['signal_score'] = self._calculate_comprehensive_score(signal_analysis)
        
        # 生成信号描述
        signal_analysis.update(self._generate_signal_description(signal_analysis))
        
        return signal_analysis
    
    def _analyze_crossover_signals(self, current_dif: float, current_dea: float,
                                  prev_dif: Optional[float], prev_dea: Optional[float]) -> Dict:
        """分析金叉死叉信号"""
        crossover_signals = {
            'is_golden_cross': False,
            'is_death_cross': False,
            'is_zero_cross_up': False,
            'is_zero_cross_down': False,
            'crossover_type': 'none',
            'crossover_position': 'unknown'
        }
        
        if prev_dif is None or prev_dea is None:
            return crossover_signals
        
        # 金叉检测: DIF从下方穿越DEA
        if current_dif > current_dea and prev_dif <= prev_dea:
            crossover_signals['is_golden_cross'] = True
            if current_dif > 0:
                crossover_signals['crossover_type'] = 'golden_cross_above_zero'
                crossover_signals['crossover_position'] = 'above_zero'
            else:
                crossover_signals['crossover_type'] = 'golden_cross_below_zero'
                crossover_signals['crossover_position'] = 'below_zero'
        
        # 死叉检测: DIF从上方穿越DEA
        elif current_dif < current_dea and prev_dif >= prev_dea:
            crossover_signals['is_death_cross'] = True
            if current_dif > 0:
                crossover_signals['crossover_type'] = 'death_cross_above_zero'
                crossover_signals['crossover_position'] = 'above_zero'
            else:
                crossover_signals['crossover_type'] = 'death_cross_below_zero'
                crossover_signals['crossover_position'] = 'below_zero'
        
        # DIF零轴穿越
        if current_dif > 0 and prev_dif <= 0:
            crossover_signals['is_zero_cross_up'] = True
            crossover_signals['zero_cross_type'] = 'dif_cross_zero_up'
        elif current_dif < 0 and prev_dif >= 0:
            crossover_signals['is_zero_cross_down'] = True
            crossover_signals['zero_cross_type'] = 'dif_cross_zero_down'
        
        return crossover_signals
    
    def _analyze_signal_strength(self, dif: float, dea: float, macd: float) -> Dict:
        """分析信号强度"""
        dif_dea_gap = abs(dif - dea)
        dif_magnitude = abs(dif)
        
        # 强度等级判断
        if dif_dea_gap >= self.thresholds['extreme_signal']:
            strength_level = 'extreme'
        elif dif_dea_gap >= self.thresholds['strong_signal']:
            strength_level = 'strong'
        elif dif_dea_gap >= self.thresholds['moderate_signal']:
            strength_level = 'moderate'
        elif dif_dea_gap >= self.thresholds['weak_signal']:
            strength_level = 'weak'
        else:
            strength_level = 'minimal'
        
        return {
            'dif_dea_gap': dif_dea_gap,
            'dif_magnitude': dif_magnitude,
            'macd_magnitude': abs(macd),
            'strength_level': strength_level,
            'is_significant_signal': dif_dea_gap >= self.thresholds['moderate_signal']
        }
    
    def _analyze_trend_status(self, dif_series: pd.Series, dea_series: pd.Series, 
                             macd_series: pd.Series) -> Dict:
        """分析趋势状态"""
        # 取最近5个数据点分析趋势
        recent_periods = min(5, len(dif_series))
        
        recent_dif = dif_series.iloc[-recent_periods:]
        recent_dea = dea_series.iloc[-recent_periods:]
        recent_macd = macd_series.iloc[-recent_periods:]
        
        # 趋势方向分析
        dif_trend = 'up' if recent_dif.iloc[-1] > recent_dif.iloc[0] else 'down'
        dea_trend = 'up' if recent_dea.iloc[-1] > recent_dea.iloc[0] else 'down'
        macd_trend = 'up' if recent_macd.iloc[-1] > recent_macd.iloc[0] else 'down'
        
        # 柱状图变化分析
        if len(recent_macd) >= 2:
            histogram_expanding = abs(recent_macd.iloc[-1]) > abs(recent_macd.iloc[-2])
        else:
            histogram_expanding = False
        
        return {
            'dif_trend': dif_trend,
            'dea_trend': dea_trend,
            'macd_trend': macd_trend,
            'histogram_expanding': histogram_expanding,
            'trend_consistency': dif_trend == dea_trend == macd_trend
        }
    
    def _calculate_comprehensive_score(self, analysis: Dict) -> float:
        """计算综合信号评分"""
        score = 0.0
        
        # 交叉信号评分
        crossover_type = analysis.get('crossover_type', 'none')
        if crossover_type in self.weights:
            score += self.weights[crossover_type]
        
        # 零轴穿越评分
        if analysis.get('is_zero_cross_up'):
            score += self.weights['dif_cross_zero_up']
        elif analysis.get('is_zero_cross_down'):
            score += self.weights['dif_cross_zero_down']
        
        # 柱状图变化评分
        if analysis.get('histogram_expanding'):
            if analysis.get('dif_above_dea'):
                score += self.weights['histogram_expanding']
            else:
                score += self.weights['histogram_contracting']
        
        # 强度调整
        strength_multiplier = {
            'extreme': 1.2,
            'strong': 1.1,
            'moderate': 1.0,
            'weak': 0.8,
            'minimal': 0.5
        }
        strength_level = analysis.get('strength_level', 'minimal')
        score *= strength_multiplier.get(strength_level, 1.0)
        
        # 限制评分范围在 -1.0 到 1.0 之间
        return max(-1.0, min(1.0, score))
    
    def _generate_signal_description(self, analysis: Dict) -> Dict:
        """生成信号描述"""
        score = analysis['signal_score']
        crossover_type = analysis.get('crossover_type', 'none')
        strength_level = analysis.get('strength_level', 'minimal')
        
        # 基础描述
        if score >= 0.7:
            description = "强势买入信号"
            suggestion = "建议买入"
            confidence = "高"
        elif score >= 0.3:
            description = "温和买入信号"
            suggestion = "可考虑买入"
            confidence = "中"
        elif score <= -0.7:
            description = "强势卖出信号"
            suggestion = "建议卖出"
            confidence = "高"
        elif score <= -0.3:
            description = "温和卖出信号"
            suggestion = "可考虑卖出"
            confidence = "中"
        else:
            description = "观望信号"
            suggestion = "保持观望"
            confidence = "低"
        
        # 特殊信号补充描述
        if analysis.get('is_golden_cross'):
            if analysis.get('crossover_position') == 'above_zero':
                description += " (零轴上方金叉)"
            else:
                description += " (零轴下方金叉)"
        elif analysis.get('is_death_cross'):
            if analysis.get('crossover_position') == 'above_zero':
                description += " (零轴上方死叉)"
            else:
                description += " (零轴下方死叉)"
        
        if analysis.get('is_zero_cross_up'):
            description += " (DIF上穿零轴)"
        elif analysis.get('is_zero_cross_down'):
            description += " (DIF下穿零轴)"
        
        return {
            'signal_description': description,
            'trade_suggestion': suggestion,
            'confidence_level': confidence
        }
    
    def _empty_signal_result(self, reason: str) -> Dict:
        """返回空的信号结果"""
        return {
            'error': reason,
            'current_dif': 0.0,
            'current_dea': 0.0,
            'current_macd': 0.0,
            'signal_score': 0.0,
            'signal_description': '数据不足',
            'trade_suggestion': '无法分析',
            'confidence_level': '无'
        }
    
    def batch_analyze_historical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """批量分析历史数据的MACD信号"""
        if 'Close' not in df.columns:
            raise ValueError("输入DataFrame必须包含'Close'列")
        
        # 先计算MACD组件
        result_df = self.macd_engine.calculate_batch_macd(df)
        
        # 添加信号分析列
        signal_scores = []
        signal_descriptions = []
        trade_suggestions = []
        confidence_levels = []
        
        for i in range(len(result_df)):
            if i < self.macd_engine.slow_period + self.macd_engine.signal_period:
                # 数据不足时填充默认值
                signal_scores.append(0.0)
                signal_descriptions.append('数据不足')
                trade_suggestions.append('无法分析')
                confidence_levels.append('无')
            else:
                # 分析当前行的信号
                historical_prices = result_df['Close'].iloc[:i].tolist()
                current_price = result_df['Close'].iloc[i]
                
                signal_result = self.analyze_single_signal(current_price, historical_prices)
                
                signal_scores.append(signal_result['signal_score'])
                signal_descriptions.append(signal_result['signal_description'])
                trade_suggestions.append(signal_result['trade_suggestion'])
                confidence_levels.append(signal_result['confidence_level'])
        
        # 添加到结果DataFrame
        result_df['MACD信号评分'] = signal_scores
        result_df['MACD信号描述'] = signal_descriptions
        result_df['交易建议'] = trade_suggestions
        result_df['信心水平'] = confidence_levels
        
        return result_df 