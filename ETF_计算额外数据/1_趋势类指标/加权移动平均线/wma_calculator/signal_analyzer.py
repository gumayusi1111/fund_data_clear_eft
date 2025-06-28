#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA信号分析器模块
================

专门负责WMA交易信号的分析和判断
"""

from typing import Dict, Optional
from .config import WMAConfig


class SignalAnalyzer:
    """WMA信号分析器"""
    
    def __init__(self, config: WMAConfig):
        """
        初始化信号分析器
        
        Args:
            config: WMA配置对象
        """
        self.config = config
        print("📊 信号分析器初始化完成")
    
    def calculate_alignment(self, wma_results: Dict[str, Optional[float]]) -> str:
        """
        计算多空排列状态
        
        Args:
            wma_results: WMA计算结果
            
        Returns:
            str: 排列状态描述
        """
        try:
            wma5 = wma_results.get('WMA_5')
            wma10 = wma_results.get('WMA_10')
            wma20 = wma_results.get('WMA_20')
            
            if not all([wma5, wma10, wma20]):
                return "数据不足"
            
            # 强势多头排列：短期 > 中期 > 长期
            if wma5 > wma10 > wma20:
                return "强势多头排列"
            # 弱势多头：部分多头特征
            elif wma5 > wma10 or wma10 > wma20:
                return "弱势多头"
            # 强势空头排列：短期 < 中期 < 长期
            elif wma5 < wma10 < wma20:
                return "强势空头排列"
            # 弱势空头：部分空头特征
            elif wma5 < wma10 or wma10 < wma20:
                return "弱势空头"
            else:
                return "中性排列"
                
        except Exception as e:
            print(f"❌ 多空排列计算失败: {e}")
            return "计算失败"
    
    def calculate_price_signals(self, current_price: float, wma_results: Dict[str, Optional[float]]) -> Dict:
        """
        计算价格相对于WMA的信号
        
        Args:
            current_price: 当前价格
            wma_results: WMA结果
            
        Returns:
            Dict: 价格信号分析
        """
        signals = {}
        
        for period in self.config.wma_periods:
            wma_key = f'WMA_{period}'
            wma_value = wma_results.get(wma_key)
            
            if wma_value:
                diff = current_price - wma_value
                diff_pct = (diff / wma_value) * 100
                
                # 判断价格位置
                if diff > 0:
                    position = "价格上方"
                    signal_strength = "看涨" if diff_pct > 1 else ("中性偏涨" if diff_pct > 0.1 else "微涨")
                elif diff < 0:
                    position = "价格下方"
                    signal_strength = "看跌" if diff_pct < -1 else ("中性偏跌" if diff_pct < -0.1 else "微跌")
                else:
                    position = "价格重合"
                    signal_strength = "中性"
                
                signals[f'vs_WMA{period}'] = {
                    'position': position,
                    'difference': round(diff, 6),
                    'difference_pct': round(diff_pct, 4),
                    'signal_strength': signal_strength
                }
        
        return signals
    
    def analyze_trend_signals(self, wma_results: Dict[str, Optional[float]]) -> Dict:
        """
        分析趋势信号
        
        Args:
            wma_results: WMA结果
            
        Returns:
            Dict: 趋势信号分析
        """
        trend_analysis = {
            'short_term_trend': '未知',
            'medium_term_trend': '未知',
            'long_term_trend': '未知',
            'overall_trend': '未知',
            'trend_consistency': 0.0
        }
        
        try:
            wma3 = wma_results.get('WMA_3')
            wma5 = wma_results.get('WMA_5')
            wma10 = wma_results.get('WMA_10')
            wma20 = wma_results.get('WMA_20')
            
            valid_wmas = [w for w in [wma3, wma5, wma10, wma20] if w is not None]
            
            if len(valid_wmas) >= 2:
                # 短期趋势 (WMA3 vs WMA5)
                if wma3 and wma5:
                    if wma3 > wma5:
                        trend_analysis['short_term_trend'] = '上升'
                    elif wma3 < wma5:
                        trend_analysis['short_term_trend'] = '下降'
                    else:
                        trend_analysis['short_term_trend'] = '平稳'
                
                # 中期趋势 (WMA5 vs WMA10)
                if wma5 and wma10:
                    if wma5 > wma10:
                        trend_analysis['medium_term_trend'] = '上升'
                    elif wma5 < wma10:
                        trend_analysis['medium_term_trend'] = '下降'
                    else:
                        trend_analysis['medium_term_trend'] = '平稳'
                
                # 长期趋势 (WMA10 vs WMA20)
                if wma10 and wma20:
                    if wma10 > wma20:
                        trend_analysis['long_term_trend'] = '上升'
                    elif wma10 < wma20:
                        trend_analysis['long_term_trend'] = '下降'
                    else:
                        trend_analysis['long_term_trend'] = '平稳'
                
                # 整体趋势判断
                trends = [trend_analysis['short_term_trend'], 
                         trend_analysis['medium_term_trend'], 
                         trend_analysis['long_term_trend']]
                valid_trends = [t for t in trends if t != '未知']
                
                if valid_trends:
                    up_count = valid_trends.count('上升')
                    down_count = valid_trends.count('下降')
                    flat_count = valid_trends.count('平稳')
                    
                    if up_count > down_count and up_count > flat_count:
                        trend_analysis['overall_trend'] = '上升趋势'
                    elif down_count > up_count and down_count > flat_count:
                        trend_analysis['overall_trend'] = '下降趋势'
                    else:
                        trend_analysis['overall_trend'] = '震荡趋势'
                    
                    # 趋势一致性
                    max_count = max(up_count, down_count, flat_count)
                    trend_analysis['trend_consistency'] = (max_count / len(valid_trends)) * 100
        
        except Exception as e:
            print(f"❌ 趋势信号分析失败: {e}")
        
        return trend_analysis
    
    def generate_trading_signals(self, current_price: float, wma_results: Dict[str, Optional[float]], 
                                alignment: str, trend_analysis: Dict) -> Dict:
        """
        生成交易信号
        
        Args:
            current_price: 当前价格
            wma_results: WMA结果
            alignment: 多空排列
            trend_analysis: 趋势分析
            
        Returns:
            Dict: 交易信号
        """
        signals = {
            'primary_signal': '观望',
            'signal_strength': 0,  # -5到5的强度
            'confidence_level': 0.0,  # 0-100的置信度
            'suggested_action': '观望',
            'risk_assessment': '中等',
            'signal_details': []
        }
        
        try:
            signal_score = 0
            signal_details = []
            
            # 多空排列信号
            if alignment == "强势多头排列":
                signal_score += 2
                signal_details.append("强势多头排列(+2)")
            elif alignment == "弱势多头":
                signal_score += 1
                signal_details.append("弱势多头(+1)")
            elif alignment == "强势空头排列":
                signal_score -= 2
                signal_details.append("强势空头排列(-2)")
            elif alignment == "弱势空头":
                signal_score -= 1
                signal_details.append("弱势空头(-1)")
            
            # 趋势一致性信号
            overall_trend = trend_analysis.get('overall_trend', '震荡趋势')
            consistency = trend_analysis.get('trend_consistency', 0)
            
            if overall_trend == '上升趋势' and consistency > 66:
                signal_score += 1
                signal_details.append(f"强上升趋势({consistency:.0f}%一致性)(+1)")
            elif overall_trend == '下降趋势' and consistency > 66:
                signal_score -= 1
                signal_details.append(f"强下降趋势({consistency:.0f}%一致性)(-1)")
            
            # 价格位置信号
            wma20 = wma_results.get('WMA_20')
            if wma20:
                price_diff_pct = ((current_price - wma20) / wma20) * 100
                if price_diff_pct > 2:
                    signal_score += 1
                    signal_details.append(f"价格远高于WMA20({price_diff_pct:.1f}%)(+1)")
                elif price_diff_pct < -2:
                    signal_score -= 1
                    signal_details.append(f"价格远低于WMA20({price_diff_pct:.1f}%)(-1)")
            
            # 生成最终信号
            signals['signal_strength'] = max(-5, min(5, signal_score))
            signals['signal_details'] = signal_details
            
            if signal_score >= 3:
                signals['primary_signal'] = '强烈买入'
                signals['suggested_action'] = '积极买入'
                signals['confidence_level'] = 80 + min(20, (signal_score - 3) * 10)
                signals['risk_assessment'] = '中低'
            elif signal_score >= 1:
                signals['primary_signal'] = '买入'
                signals['suggested_action'] = '谨慎买入'
                signals['confidence_level'] = 60 + (signal_score - 1) * 10
                signals['risk_assessment'] = '中等'
            elif signal_score <= -3:
                signals['primary_signal'] = '强烈卖出'
                signals['suggested_action'] = '积极卖出'
                signals['confidence_level'] = 80 + min(20, abs(signal_score + 3) * 10)
                signals['risk_assessment'] = '中低'
            elif signal_score <= -1:
                signals['primary_signal'] = '卖出'
                signals['suggested_action'] = '谨慎卖出'
                signals['confidence_level'] = 60 + abs(signal_score + 1) * 10
                signals['risk_assessment'] = '中等'
            else:
                signals['primary_signal'] = '观望'
                signals['suggested_action'] = '持有观望'
                signals['confidence_level'] = 50
                signals['risk_assessment'] = '中等'
        
        except Exception as e:
            print(f"❌ 交易信号生成失败: {e}")
        
        return signals 