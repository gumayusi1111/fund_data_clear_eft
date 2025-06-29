#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA信号分析器 - 科学改进版
========================

基于学术研究的科学EMA多空排列算法
采用统计显著性阈值和相对差距分析，与WMA/SMA系统保持一致
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .config import EMAConfig
from .ema_engine import EMAEngine


class SignalAnalyzer:
    """EMA信号分析器 - 科学改进版"""
    
    def __init__(self, config: EMAConfig):
        """
        初始化信号分析器
        
        Args:
            config: EMA配置对象
        """
        self.config = config
        self.ema_engine = EMAEngine(config)
        
        # 🎯 使用EMA系统专属参数（快速响应系统）
        self.thresholds = config.get_system_thresholds()
        self.score_weights = config.get_system_score_weights()
        self.volume_threshold = config.get_volume_threshold()
        self.tolerance_ratio = config.get_tolerance_ratio()
        
        print("🎯 EMA信号分析器初始化完成 (系统差异化版)")
        print(f"🎯 EMA专属阈值: {self.thresholds}")
        print(f"📊 EMA专属权重: {self.score_weights}")
        print(f"📈 量能阈值: {self.volume_threshold}, 容错率: {self.tolerance_ratio}")
    
    def _calculate_relative_gap(self, value_short: float, value_long: float) -> float:
        """
        计算相对差距百分比
        
        Args:
            value_short: 短期值（价格、短期EMA等）
            value_long: 长期值（长期EMA等）
            
        Returns:
            float: 相对差距百分比
        """
        if value_long <= 0:
            return 0.0
        return ((value_short - value_long) / value_long) * 100
    
    def _classify_strength(self, gap_pct: float) -> str:
        """
        基于统计显著性分类强度
        
        Args:
            gap_pct: 差距百分比
            
        Returns:
            str: 强度等级
        """
        abs_gap = abs(gap_pct)
        
        if abs_gap < self.thresholds['minimal']:
            return "微弱"
        elif abs_gap < self.thresholds['moderate']:
            return "温和"
        elif abs_gap < self.thresholds['strong']:
            return "中等"
        else:
            return "强势"
    
    def _scientific_ema_alignment_analysis(self, current_price: float, 
                                         ema12: float, ema26: float) -> Tuple[str, float, Dict]:
        """
        科学的EMA多空排列分析 - 使用EMA系统专属参数
        
        Args:
            current_price: 当前价格
            ema12: 12日指数移动平均线
            ema26: 26日指数移动平均线
            
        Returns:
            Tuple[str, float, Dict]: (排列状态, 评分, 详细分析)
        """
        details = {
            'price_ema12_pct': 0.0,
            'ema12_ema26_pct': 0.0,
            'avg_gap_pct': 0.0,
            'min_gap_pct': 0.0,
            'statistical_significance': False,
            'strength_level': '微弱',
            'direction': '震荡',
            'scientific_basis': f'基于EMA系统专属参数 (快速响应{self.thresholds["minimal"]}%)',
            'system_type': 'EMA (快速响应)'
        }
        
        # 计算相对差距
        price_ema12_gap = self._calculate_relative_gap(current_price, ema12)
        ema12_ema26_gap = self._calculate_relative_gap(ema12, ema26)
        details['price_ema12_pct'] = price_ema12_gap
        details['ema12_ema26_pct'] = ema12_ema26_gap
        
        # 统计显著性检验
        primary_gaps = [price_ema12_gap, ema12_ema26_gap]
        avg_gap = sum([abs(gap) for gap in primary_gaps]) / len(primary_gaps)
        min_gap = min([abs(gap) for gap in primary_gaps])
        
        details['avg_gap_pct'] = avg_gap
        details['min_gap_pct'] = min_gap
        
        # 🔬 核心：统计显著性检验（使用EMA系统专属阈值）
        if min_gap < self.thresholds['noise_filter']:
            # 差距太小，视为市场噪音
            details['statistical_significance'] = False
            return "震荡排列", 0.0, details
        
        details['statistical_significance'] = True
        
        # EMA特有的排列逻辑：价格 > EMA12 > EMA26 (多头) 或相反 (空头)
        if (price_ema12_gap > self.thresholds['minimal'] and 
            ema12_ema26_gap > self.thresholds['minimal']):
            # 多头排列：价格 > EMA12 > EMA26
            direction = '多头'
            strength = self._classify_strength(avg_gap)
            status = f"{strength}多头排列"
            
            base_score = self.score_weights[strength]
            
            # EMA特有奖励：如果价格远高于EMA12，额外加成
            if price_ema12_gap > 2.0:
                base_score *= 1.1  # 价格强势突破加成
            
            final_score = base_score
            
        elif (price_ema12_gap < -self.thresholds['minimal'] and 
              ema12_ema26_gap < -self.thresholds['minimal']):
            # 空头排列：价格 < EMA12 < EMA26
            direction = '空头'
            strength = self._classify_strength(avg_gap)
            status = f"{strength}空头排列"
            
            base_score = self.score_weights[strength]
            
            # EMA特有惩罚：如果价格远低于EMA12，额外减分
            if price_ema12_gap < -2.0:
                base_score *= 1.1  # 价格弱势突破加成
            
            final_score = -base_score  # 空头为负分
            
        else:
            # 方向不一致，视为震荡
            direction = '震荡'
            if price_ema12_gap > 0 and ema12_ema26_gap < 0:
                status = "价格强于EMA12但EMA12弱于EMA26"
            elif price_ema12_gap < 0 and ema12_ema26_gap > 0:
                status = "价格弱于EMA12但EMA12强于EMA26"
            else:
                status = "EMA信号分化"
            final_score = 0.0
            strength = "微弱"
        
        # 质量评估：与WMA/SMA一致的质量判断
        if avg_gap < self.thresholds['minimal']:
            final_score *= 0.5  # 差距过小，信号质量折扣
        elif avg_gap > 2.0:
            final_score *= 1.1  # 差距明显，信号质量提升
        
        details['strength_level'] = strength
        details['direction'] = direction
        
        return status, round(final_score, 2), details
    
    def analyze_ema_arrangement(self, df: pd.DataFrame, ema_values: Dict = None) -> Dict:
        """
        分析EMA多空排列 - 科学改进版
        
        Args:
            df: ETF数据
            ema_values: 预计算的EMA值（避免重复计算）
            
        Returns:
            Dict: 排列分析结果
        """
        try:
            if df.empty or len(df) < max(self.config.ema_periods):
                return {
                    'arrangement': '数据不足',
                    'score': 0.0,
                    'strength_level': '未知',
                    'details': {'error': '历史数据不足'}
                }
            
            # 获取最新价格和EMA值
            current_price = float(df['收盘价'].iloc[-1])
            if ema_values is None:
                ema_values = self.ema_engine.calculate_ema_values(df)
            
            if 'ema_12' not in ema_values or 'ema_26' not in ema_values:
                return {
                    'arrangement': 'EMA计算失败',
                    'score': 0.0,
                    'strength_level': '未知',
                    'details': {'error': '无法计算EMA值'}
                }
            
            ema12 = ema_values['ema_12']
            ema26 = ema_values['ema_26']
            
            # 🔬 科学分析
            arrangement, score, details = self._scientific_ema_alignment_analysis(
                current_price, ema12, ema26
            )
            
            # 构建返回结果
            return {
                'arrangement': arrangement,
                'score': score,
                'strength_level': details['strength_level'],
                'details': details,
                'current_price': current_price,
                'ema12': ema12,
                'ema26': ema26,
                'description': f'价格:{current_price:.3f}, EMA12:{ema12:.3f}, EMA26:{ema26:.3f}'
            }
            
        except Exception as e:
            print(f"❌ EMA排列分析失败: {str(e)}")
            return {
                'arrangement': '分析失败',
                'score': 0.0,
                'strength_level': '未知',
                'details': {'error': str(e)}
            }
    
    def get_trading_signals(self, df: pd.DataFrame, ema_values: Dict = None) -> Dict:
        """
        获取综合交易信号 - 科学改进版
        
        Args:
            df: ETF数据
            ema_values: 预计算的EMA值（避免重复计算）
            
        Returns:
            Dict: 交易信号结果
        """
        try:
            # 1. 预计算EMA值（只计算一次）
            if ema_values is None:
                ema_values = self.ema_engine.calculate_ema_values(df)
            
            # 2. EMA排列分析（科学版）
            arrangement_result = self.analyze_ema_arrangement(df, ema_values)
            
            # 3. 基础EMA信号（传入预计算的EMA值）
            basic_signals = self.ema_engine.calculate_ema_signals(df, ema_values)
            
            # 4. 综合评分（降低权重，更加保守）
            arrangement_score = arrangement_result.get('score', 0)
            basic_score = basic_signals.get('strength', 0)
            
            # 🔬 科学权重分配：EMA排列占主导，但权重降低
            total_score = arrangement_score * 0.5 + basic_score * 0.3
            
            # 5. EMA差值信号
            ema_diff = ema_values.get('ema_diff_12_26', 0)
            ema_diff_pct = ema_values.get('ema_diff_12_26_pct', 0)
            
            # 添加EMA差值评分
            if abs(ema_diff_pct) > 1.0:
                diff_bonus = 0.5 if ema_diff_pct > 0 else -0.5
                total_score += diff_bonus
            elif abs(ema_diff_pct) > 0.5:
                diff_bonus = 0.3 if ema_diff_pct > 0 else -0.3
                total_score += diff_bonus
            
            # 6. 最终建议（更加保守的阈值）
            if total_score >= 1.5:
                final_signal = '买入'
                action = 'BUY'
                confidence = min(85, 60 + abs(total_score) * 8)
            elif total_score >= 0.5:
                final_signal = '谨慎买入'
                action = 'BUY_WEAK'
                confidence = min(70, 50 + abs(total_score) * 8)
            elif total_score <= -1.5:
                final_signal = '卖出'
                action = 'SELL'
                confidence = min(85, 60 + abs(total_score) * 8)
            elif total_score <= -0.5:
                final_signal = '谨慎卖出'
                action = 'SELL_WEAK'
                confidence = min(70, 50 + abs(total_score) * 8)
            else:
                final_signal = '观望'
                action = 'HOLD'
                confidence = 50
            
            return {
                'final_signal': final_signal,
                'action': action,
                'confidence': int(confidence),
                'total_score': round(total_score, 2),
                'arrangement': arrangement_result,
                'basic_signals': basic_signals,
                'ema_diff': ema_diff,
                'ema_diff_pct': ema_diff_pct
            }
            
        except Exception as e:
            print(f"❌ EMA交易信号分析失败: {str(e)}")
            return {
                'final_signal': '分析失败',
                'action': 'ERROR',
                'confidence': 0,
                'total_score': 0,
                'error': str(e)
            }
    
    def format_signal_display(self, signals: Dict) -> str:
        """
        格式化信号显示
        
        Args:
            signals: 信号数据
            
        Returns:
            str: 格式化的显示文本
        """
        try:
            final_signal = signals.get('final_signal', '未知')
            confidence = signals.get('confidence', 0)
            score = signals.get('total_score', 0)
            
            # 趋势图标
            if score > 0.8:
                icon = '📈'
            elif score < -0.8:
                icon = '📉'
            else:
                icon = '➡️'
            
            return f"{icon} {final_signal} (评分: {score}, 置信度: {confidence}%)"
            
        except Exception:
            return "❓ 信号显示失败" 