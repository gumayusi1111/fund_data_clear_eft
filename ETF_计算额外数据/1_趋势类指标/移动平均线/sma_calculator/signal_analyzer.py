#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA信号分析器模块 - 中短线专版
============================

专门负责SMA交易信号的分析和判断
专注于中短线交易信号：MA5, MA10, MA20, MA60
"""

from typing import Dict, Optional
from .config import SMAConfig


class SignalAnalyzer:
    """SMA信号分析器 - 中短线专版"""
    
    def __init__(self, config: SMAConfig):
        """
        初始化信号分析器
        
        Args:
            config: SMA配置对象
        """
        self.config = config
        print("📊 信号分析器初始化完成 (SMA中短线专版)")
    
    def calculate_alignment(self, sma_results: Dict[str, Optional[float]]) -> str:
        """
        计算多空排列状态 - 中短线专版
        
        Args:
            sma_results: SMA计算结果
            
        Returns:
            str: 排列状态描述
        """
        try:
            sma5 = sma_results.get('SMA_5')
            sma10 = sma_results.get('SMA_10')
            sma20 = sma_results.get('SMA_20')
            sma60 = sma_results.get('SMA_60')
            
            # 确保至少有3个有效的SMA值
            valid_smas = [sma for sma in [sma5, sma10, sma20, sma60] if sma is not None]
            if len(valid_smas) < 3:
                return "数据不足"
            
            # 🎯 中短线多空排列判断
            # 强势多头排列：MA5 > MA10 > MA20 > MA60
            if all([
                sma5 is not None, sma10 is not None, sma20 is not None,
                sma5 > sma10 > sma20
            ]):
                if sma60 is not None and sma20 > sma60:
                    return "强势多头排列"
                else:
                    return "中期多头排列"
            
            # 强势空头排列：MA5 < MA10 < MA20 < MA60  
            elif all([
                sma5 is not None, sma10 is not None, sma20 is not None,
                sma5 < sma10 < sma20
            ]):
                if sma60 is not None and sma20 < sma60:
                    return "强势空头排列"
                else:
                    return "中期空头排列"
            
            # 短期多头：MA5 > MA10，但MA20可能交叉
            elif sma5 is not None and sma10 is not None and sma5 > sma10:
                if sma20 is not None and sma10 > sma20:
                    return "短期多头排列"
                else:
                    return "弱势多头"
            
            # 短期空头：MA5 < MA10，但MA20可能交叉
            elif sma5 is not None and sma10 is not None and sma5 < sma10:
                if sma20 is not None and sma10 < sma20:
                    return "短期空头排列"
                else:
                    return "弱势空头"
            
            else:
                return "震荡排列"
                
        except Exception as e:
            print(f"❌ 多空排列计算失败: {e}")
            return "计算失败"
    
    def calculate_price_signals(self, current_price: float, sma_results: Dict[str, Optional[float]]) -> Dict:
        """
        计算价格相对于SMA的信号
        
        Args:
            current_price: 当前价格
            sma_results: SMA结果
            
        Returns:
            Dict: 价格信号分析
        """
        signals = {}
        
        for period in self.config.sma_periods:
            sma_key = f'SMA_{period}'
            sma_value = sma_results.get(sma_key)
            
            if sma_value:
                diff = current_price - sma_value
                diff_pct = (diff / sma_value) * 100
                
                # 判断价格位置和信号强度
                if diff > 0:
                    position = "价格上方"
                    if diff_pct > 2:
                        signal_strength = "强势看涨"
                    elif diff_pct > 1:
                        signal_strength = "温和看涨"
                    elif diff_pct > 0.1:
                        signal_strength = "中性偏涨"
                    else:
                        signal_strength = "微涨"
                elif diff < 0:
                    position = "价格下方"
                    if diff_pct < -2:
                        signal_strength = "强势看跌"
                    elif diff_pct < -1:
                        signal_strength = "温和看跌"
                    elif diff_pct < -0.1:
                        signal_strength = "中性偏跌"
                    else:
                        signal_strength = "微跌"
                else:
                    position = "价格重合"
                    signal_strength = "中性"
                
                signals[f'vs_MA{period}'] = {
                    'position': position,
                    'difference': round(diff, 6),
                    'difference_pct': round(diff_pct, 4),
                    'signal_strength': signal_strength
                }
        
        return signals
    
    def analyze_trend_signals(self, sma_results: Dict[str, Optional[float]]) -> Dict:
        """
        分析趋势信号 - 中短线专版
        
        Args:
            sma_results: SMA结果
            
        Returns:
            Dict: 趋势信号分析
        """
        trend_analysis = {
            'short_term_trend': '未知',
            'medium_term_trend': '未知',
            'overall_trend': '未知',
            'trend_consistency': 0.0
        }
        
        try:
            sma5 = sma_results.get('SMA_5')
            sma10 = sma_results.get('SMA_10')
            sma20 = sma_results.get('SMA_20')
            sma60 = sma_results.get('SMA_60')
            
            # 短期趋势分析 (MA5 vs MA10)
            if sma5 is not None and sma10 is not None:
                diff_5_10 = (sma5 - sma10) / sma10 * 100
                if diff_5_10 > 0.5:
                    trend_analysis['short_term_trend'] = '强势上升'
                elif diff_5_10 > 0:
                    trend_analysis['short_term_trend'] = '温和上升'
                elif diff_5_10 < -0.5:
                    trend_analysis['short_term_trend'] = '强势下降'
                elif diff_5_10 < 0:
                    trend_analysis['short_term_trend'] = '温和下降'
                else:
                    trend_analysis['short_term_trend'] = '横盘整理'
            
            # 中期趋势分析 (MA10 vs MA20)
            if sma10 is not None and sma20 is not None:
                diff_10_20 = (sma10 - sma20) / sma20 * 100
                if diff_10_20 > 1:
                    trend_analysis['medium_term_trend'] = '强势上升'
                elif diff_10_20 > 0:
                    trend_analysis['medium_term_trend'] = '温和上升'
                elif diff_10_20 < -1:
                    trend_analysis['medium_term_trend'] = '强势下降'
                elif diff_10_20 < 0:
                    trend_analysis['medium_term_trend'] = '温和下降'
                else:
                    trend_analysis['medium_term_trend'] = '横盘整理'
            
            # 总体趋势综合判断
            short_score = 0
            medium_score = 0
            
            if '上升' in trend_analysis['short_term_trend']:
                short_score = 2 if '强势' in trend_analysis['short_term_trend'] else 1
            elif '下降' in trend_analysis['short_term_trend']:
                short_score = -2 if '强势' in trend_analysis['short_term_trend'] else -1
            
            if '上升' in trend_analysis['medium_term_trend']:
                medium_score = 2 if '强势' in trend_analysis['medium_term_trend'] else 1
            elif '下降' in trend_analysis['medium_term_trend']:
                medium_score = -2 if '强势' in trend_analysis['medium_term_trend'] else -1
            
            total_score = short_score + medium_score
            
            if total_score >= 3:
                trend_analysis['overall_trend'] = '强势上涨'
            elif total_score >= 1:
                trend_analysis['overall_trend'] = '温和上涨'
            elif total_score <= -3:
                trend_analysis['overall_trend'] = '强势下跌'
            elif total_score <= -1:
                trend_analysis['overall_trend'] = '温和下跌'
            else:
                trend_analysis['overall_trend'] = '震荡整理'
            
            # 趋势一致性评分
            consistency_score = abs(short_score) + abs(medium_score)
            if short_score * medium_score > 0:  # 同向
                trend_analysis['trend_consistency'] = min(100, consistency_score * 25)
            else:  # 反向
                trend_analysis['trend_consistency'] = max(0, 50 - abs(short_score - medium_score) * 10)
                
        except Exception as e:
            print(f"❌ 趋势信号分析失败: {e}")
        
        return trend_analysis
    
    def generate_trading_signals(self, current_price: float, sma_results: Dict[str, Optional[float]], 
                                alignment: str, trend_analysis: Dict) -> Dict:
        """
        生成交易信号 - 中短线专版
        
        Args:
            current_price: 当前价格
            sma_results: SMA结果
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
                signal_score += 3
                signal_details.append("强势多头排列(+3)")
            elif alignment == "中期多头排列":
                signal_score += 2
                signal_details.append("中期多头排列(+2)")
            elif alignment == "短期多头排列":
                signal_score += 1
                signal_details.append("短期多头排列(+1)")
            elif alignment == "强势空头排列":
                signal_score -= 3
                signal_details.append("强势空头排列(-3)")
            elif alignment == "中期空头排列":
                signal_score -= 2
                signal_details.append("中期空头排列(-2)")
            elif alignment == "短期空头排列":
                signal_score -= 1
                signal_details.append("短期空头排列(-1)")
            
            # SMA差值信号分析
            smadiff_5_20 = sma_results.get('SMA_DIFF_5_20')
            smadiff_5_20_pct = sma_results.get('SMA_DIFF_5_20_PCT')
            
            if smadiff_5_20 is not None and smadiff_5_20_pct is not None:
                # 基于相对差值百分比的信号
                if smadiff_5_20_pct > 1.5:  # 相对差值超过1.5%，强烈上升信号
                    signal_score += 2
                    signal_details.append(f"SMA差值强势上升({smadiff_5_20_pct:+.2f}%)(+2)")
                elif smadiff_5_20_pct > 0.5:  # 相对差值超过0.5%，温和上升信号
                    signal_score += 1
                    signal_details.append(f"SMA差值温和上升({smadiff_5_20_pct:+.2f}%)(+1)")
                elif smadiff_5_20_pct < -1.5:  # 相对差值低于-1.5%，强烈下降信号
                    signal_score -= 2
                    signal_details.append(f"SMA差值强势下降({smadiff_5_20_pct:+.2f}%)(-2)")
                elif smadiff_5_20_pct < -0.5:  # 相对差值低于-0.5%，温和下降信号
                    signal_score -= 1
                    signal_details.append(f"SMA差值温和下降({smadiff_5_20_pct:+.2f}%)(-1)")
            
            # 短期差值信号 (SMA5-10)
            smadiff_5_10 = sma_results.get('SMA_DIFF_5_10')
            if smadiff_5_10 is not None:
                sma10 = sma_results.get('SMA_10')
                if sma10 is not None and sma10 > 0:
                    diff_pct = (smadiff_5_10 / sma10) * 100
                    if diff_pct > 0.3:
                        signal_score += 0.5
                        signal_details.append(f"短期动量向上({diff_pct:+.2f}%)(+0.5)")
                    elif diff_pct < -0.3:
                        signal_score -= 0.5
                        signal_details.append(f"短期动量向下({diff_pct:+.2f}%)(-0.5)")
            
            # 趋势一致性加分
            trend_consistency = trend_analysis.get('trend_consistency', 0)
            if trend_consistency > 80:
                consistency_bonus = 1
                signal_details.append(f"趋势高度一致(+1)")
                signal_score += consistency_bonus
            elif trend_consistency > 60:
                consistency_bonus = 0.5
                signal_details.append(f"趋势较为一致(+0.5)")
                signal_score += consistency_bonus
            
            # 限制信号强度范围
            signal_score = max(-5, min(5, signal_score))
            
            # 生成最终信号
            if signal_score >= 4:
                signals['primary_signal'] = '强烈买入'
                signals['suggested_action'] = '建议买入'
                signals['confidence_level'] = min(95, 70 + signal_score * 5)
                signals['risk_assessment'] = '低风险'
            elif signal_score >= 2:
                signals['primary_signal'] = '买入'
                signals['suggested_action'] = '可考虑买入'
                signals['confidence_level'] = min(85, 60 + signal_score * 5)
                signals['risk_assessment'] = '中低风险'
            elif signal_score >= 1:
                signals['primary_signal'] = '弱势买入'
                signals['suggested_action'] = '谨慎买入'
                signals['confidence_level'] = min(75, 50 + signal_score * 5)
                signals['risk_assessment'] = '中等风险'
            elif signal_score <= -4:
                signals['primary_signal'] = '强烈卖出'
                signals['suggested_action'] = '建议卖出'
                signals['confidence_level'] = min(95, 70 + abs(signal_score) * 5)
                signals['risk_assessment'] = '高风险'
            elif signal_score <= -2:
                signals['primary_signal'] = '卖出'
                signals['suggested_action'] = '可考虑卖出'
                signals['confidence_level'] = min(85, 60 + abs(signal_score) * 5)
                signals['risk_assessment'] = '中高风险'
            elif signal_score <= -1:
                signals['primary_signal'] = '弱势卖出'
                signals['suggested_action'] = '谨慎卖出'
                signals['confidence_level'] = min(75, 50 + abs(signal_score) * 5)
                signals['risk_assessment'] = '中等风险'
            else:
                signals['primary_signal'] = '观望'
                signals['suggested_action'] = '持有观望'
                signals['confidence_level'] = 60
                signals['risk_assessment'] = '中等风险'
            
            signals['signal_strength'] = signal_score
            signals['signal_details'] = signal_details
            
        except Exception as e:
            print(f"❌ 交易信号生成失败: {e}")
        
        return signals 