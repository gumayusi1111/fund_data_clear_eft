#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA信号分析器 - 中短期专版
========================

专门分析EMA指标的交易信号
提供多维度的信号评估和交易建议
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .config import EMAConfig
from .ema_engine import EMAEngine


class SignalAnalyzer:
    """EMA信号分析器 - 中短期专版"""
    
    def __init__(self, config: EMAConfig):
        """
        初始化信号分析器
        
        Args:
            config: EMA配置对象
        """
        self.config = config
        self.ema_engine = EMAEngine(config)
        print("🎯 EMA信号分析器初始化完成")
    
    def analyze_ema_arrangement(self, df: pd.DataFrame, ema_values: Dict = None) -> Dict:
        """
        分析EMA多空排列
        
        Args:
            df: ETF数据
            ema_values: 预计算的EMA值（避免重复计算）
            
        Returns:
            Dict: 排列分析结果
        """
        try:
            if df.empty or len(df) < max(self.config.ema_periods):
                return {'arrangement': '数据不足', 'score': 0, 'description': '历史数据不足'}
            
            # 获取最新价格和EMA值
            current_price = float(df['收盘价'].iloc[-1])
            if ema_values is None:
                ema_values = self.ema_engine.calculate_ema_values(df)
            
            if 'ema_12' not in ema_values or 'ema_26' not in ema_values:
                return {'arrangement': 'EMA计算失败', 'score': 0, 'description': '无法计算EMA值'}
            
            ema12 = ema_values['ema_12']
            ema26 = ema_values['ema_26']
            
            # 判断排列类型
            if current_price > ema12 > ema26:
                arrangement = '强势多头排列'
                score = 3
                description = f'价格({current_price:.3f}) > EMA12({ema12:.3f}) > EMA26({ema26:.3f})'
            elif current_price > ema12 and ema12 < ema26:
                arrangement = '弱势多头排列'
                score = 1
                description = f'价格({current_price:.3f}) > EMA12({ema12:.3f}) 但 EMA12 < EMA26({ema26:.3f})'
            elif current_price < ema12 < ema26:
                arrangement = '强势空头排列'
                score = -3
                description = f'价格({current_price:.3f}) < EMA12({ema12:.3f}) < EMA26({ema26:.3f})'
            elif current_price < ema12 and ema12 > ema26:
                arrangement = '弱势空头排列'
                score = -1
                description = f'价格({current_price:.3f}) < EMA12({ema12:.3f}) 但 EMA12 > EMA26({ema26:.3f})'
            else:
                arrangement = '震荡排列'
                score = 0
                description = f'EMA排列不明确，当前处于震荡状态'
            
            return {
                'arrangement': arrangement,
                'score': score,
                'description': description,
                'current_price': current_price,
                'ema12': ema12,
                'ema26': ema26
            }
            
        except Exception as e:
            print(f"⚠️  EMA排列分析失败: {str(e)}")
            return {'arrangement': '分析失败', 'score': 0, 'description': str(e)}
    
    def get_trading_signals(self, df: pd.DataFrame, ema_values: Dict = None) -> Dict:
        """
        获取综合交易信号
        
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
            
            # 2. EMA排列分析
            arrangement = self.analyze_ema_arrangement(df, ema_values)
            
            # 3. 基础EMA信号（传入预计算的EMA值）
            basic_signals = self.ema_engine.calculate_ema_signals(df, ema_values)
            
            # 4. 综合评分
            arrangement_score = arrangement.get('score', 0)
            basic_score = basic_signals.get('strength', 0)
            
            total_score = arrangement_score * 0.6 + basic_score * 0.4
            
            # 5. 最终建议
            if total_score >= 2:
                final_signal = '买入'
                action = 'BUY'
                confidence = min(85, 60 + abs(total_score) * 5)
            elif total_score >= 0.5:
                final_signal = '谨慎买入'
                action = 'BUY_WEAK'
                confidence = min(70, 50 + abs(total_score) * 5)
            elif total_score <= -2:
                final_signal = '卖出'
                action = 'SELL'
                confidence = min(85, 60 + abs(total_score) * 5)
            elif total_score <= -0.5:
                final_signal = '谨慎卖出'
                action = 'SELL_WEAK'
                confidence = min(70, 50 + abs(total_score) * 5)
            else:
                final_signal = '观望'
                action = 'HOLD'
                confidence = 50
            
            return {
                'final_signal': final_signal,
                'action': action,
                'confidence': int(confidence),
                'total_score': round(total_score, 2),
                'arrangement': arrangement,
                'basic_signals': basic_signals
            }
            
        except Exception as e:
            print(f"❌ 交易信号分析失败: {str(e)}")
            return {
                'final_signal': '分析失败',
                'action': 'ERROR',
                'confidence': 0,
                'total_score': 0
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
            if score > 1:
                icon = '📈'
            elif score < -1:
                icon = '📉'
            else:
                icon = '➡️'
            
            return f"{icon} {final_signal} (评分: {score}, 置信度: {confidence}%)"
            
        except Exception:
            return "❓ 信号显示失败" 