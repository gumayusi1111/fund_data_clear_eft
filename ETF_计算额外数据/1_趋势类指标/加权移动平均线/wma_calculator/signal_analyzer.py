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
        
        # 🎯 使用WMA系统专属参数（最敏感系统）
        self.thresholds = config.get_system_thresholds()
        self.score_weights = config.get_system_score_weights()
        self.volume_threshold = config.get_volume_threshold()
        self.tolerance_ratio = config.get_tolerance_ratio()
        
        print("📊 WMA信号分析器初始化完成 (系统差异化版)")
        print(f"🎯 WMA专属阈值: {self.thresholds}")
        print(f"📊 WMA专属权重: {self.score_weights}")
        print(f"📈 量能阈值: {self.volume_threshold}, 容错率: {self.tolerance_ratio}")
    
    def calculate_alignment(self, wma_results: Dict[str, Optional[float]]) -> Dict:
        """
        🔬 科学的多空排列计算 - 使用WMA系统专属参数
        
        Args:
            wma_results: WMA计算结果
            
        Returns:
            Dict: 包含排列状态、强度评分和详细分析的字典
        """
        try:
            wma5 = wma_results.get('WMA_5')
            wma10 = wma_results.get('WMA_10')
            wma20 = wma_results.get('WMA_20')
            
            if not all([wma5, wma10, wma20]):
                return {
                    'status': '数据不足',
                    'score': 0,
                    'strength_level': '无效',
                    'details': '缺少必要的WMA数据'
                }
            
            # 🎯 使用WMA系统专属阈值（比标准更严格）
            MIN_THRESHOLD_PCT = self.thresholds['minimal']      # 0.20% (比标准0.3%更严格)
            MODERATE_THRESHOLD_PCT = self.thresholds['moderate'] # 0.60% (比标准0.8%更严格)
            STRONG_THRESHOLD_PCT = self.thresholds['strong']     # 1.20% (比标准1.5%更严格)
            
            # 计算相对差距百分比
            diff_5_10_pct = ((wma5 - wma10) / wma10) * 100 if wma10 != 0 else 0
            diff_10_20_pct = ((wma10 - wma20) / wma20) * 100 if wma20 != 0 else 0
            
            # 平均差距和最小差距
            avg_diff_pct = abs((diff_5_10_pct + diff_10_20_pct) / 2)
            min_diff_pct = min(abs(diff_5_10_pct), abs(diff_10_20_pct))
            
            # 判断排列方向
            is_bullish = diff_5_10_pct > 0 and diff_10_20_pct > 0
            is_bearish = diff_5_10_pct < 0 and diff_10_20_pct < 0
            
            if not (is_bullish or is_bearish):
                return {
                    'status': '震荡排列',
                    'score': 0,
                    'strength_level': '中性',
                    'details': {
                        'diff_5_10_pct': round(diff_5_10_pct, 3),
                        'diff_10_20_pct': round(diff_10_20_pct, 3),
                        'reason': '移动平均线交织，方向不明确'
                    }
                }
            
            # 🔬 基于WMA系统专属阈值判断强度等级
            if min_diff_pct < MIN_THRESHOLD_PCT:
                strength_level = "微弱"
                base_score = self.score_weights['微弱']
            elif avg_diff_pct >= STRONG_THRESHOLD_PCT:
                strength_level = "强势"
                base_score = self.score_weights['强势']
            elif avg_diff_pct >= MODERATE_THRESHOLD_PCT:
                strength_level = "中等"
                base_score = self.score_weights['中等']
            else:
                strength_level = "温和"
                base_score = self.score_weights['温和']
            
            # 应用方向
            final_score = base_score if is_bullish else -base_score
            direction = "多头" if is_bullish else "空头"
            status = f"{strength_level}{direction}排列"
            
            return {
                'status': status,
                'score': round(final_score, 2),
                'strength_level': strength_level,
                'details': {
                    'diff_5_10_pct': round(diff_5_10_pct, 3),
                    'diff_10_20_pct': round(diff_10_20_pct, 3),
                    'avg_diff_pct': round(avg_diff_pct, 3),
                    'min_diff_pct': round(min_diff_pct, 3),
                    'direction': direction,
                    'wma_values': [round(wma5, 4), round(wma10, 4), round(wma20, 4)],
                    'scientific_basis': f'基于WMA系统专属参数 (严格阈值{MIN_THRESHOLD_PCT}%)',
                    'system_type': 'WMA (最敏感)'
                }
            }
                
        except Exception as e:
            print(f"❌ WMA多空排列计算失败: {e}")
            return {
                'status': '计算失败',
                'score': 0,
                'strength_level': '错误',
                'details': f'计算错误: {str(e)}'
            }
    
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
                                alignment: Dict, trend_analysis: Dict) -> Dict:
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
            
            # 🔬 科学的多空排列信号评分（大幅降低权重）
            alignment_status = alignment.get('status', '未知')
            alignment_score = alignment.get('score', 0)
            strength_level = alignment.get('strength_level', '未知')
            
            # 直接使用科学计算的评分，而不是固定的+2分
            if alignment_score != 0:
                signal_score += alignment_score
                direction = "多头" if alignment_score > 0 else "空头"
                signal_details.append(f"{strength_level}{direction}排列({alignment_score:+.2f})")
            
            # 🆕 添加排列质量评估
            if 'details' in alignment and isinstance(alignment['details'], dict):
                details = alignment['details']
                min_diff_pct = details.get('min_diff_pct', 0)
                avg_diff_pct = details.get('avg_diff_pct', 0)
                
                # 如果差距过小，给予额外的质量惩罚
                if min_diff_pct < 0.2:  # 小于0.2%的差距视为噪音
                    quality_penalty = -0.3
                    signal_score += quality_penalty
                    signal_details.append(f"排列质量较低(差距{min_diff_pct:.2f}%)({quality_penalty:+.1f})")
                elif avg_diff_pct > 2.0:  # 大于2%的差距给予质量奖励
                    quality_bonus = 0.2
                    signal_score += quality_bonus
                    signal_details.append(f"排列质量优秀(平均差距{avg_diff_pct:.2f}%)({quality_bonus:+.1f})")
            
            # 🆕 WMA差值信号分析
            wmadiff_5_20 = wma_results.get('WMA_DIFF_5_20')
            wmadiff_5_20_pct = wma_results.get('WMA_DIFF_5_20_PCT')
            
            if wmadiff_5_20 is not None and wmadiff_5_20_pct is not None:
                # 基于绝对差值的信号
                if wmadiff_5_20 > 0.01:  # 显著正差值
                    signal_score += 1
                    signal_details.append(f"WMA差值显著为正({wmadiff_5_20:+.4f})(+1)")
                elif wmadiff_5_20 < -0.01:  # 显著负差值
                    signal_score -= 1
                    signal_details.append(f"WMA差值显著为负({wmadiff_5_20:+.4f})(-1)")
                
                # 基于相对差值百分比的信号（更重要）
                if wmadiff_5_20_pct > 1.0:  # 相对差值超过1%，强烈上升信号
                    signal_score += 1
                    signal_details.append(f"WMA相对差值强烈上升({wmadiff_5_20_pct:+.2f}%)(+1)")
                elif wmadiff_5_20_pct > 0.5:  # 相对差值超过0.5%，温和上升信号
                    signal_score += 0.5
                    signal_details.append(f"WMA相对差值温和上升({wmadiff_5_20_pct:+.2f}%)(+0.5)")
                elif wmadiff_5_20_pct < -1.0:  # 相对差值低于-1%，强烈下降信号
                    signal_score -= 1
                    signal_details.append(f"WMA相对差值强烈下降({wmadiff_5_20_pct:+.2f}%)(-1)")
                elif wmadiff_5_20_pct < -0.5:  # 相对差值低于-0.5%，温和下降信号
                    signal_score -= 0.5
                    signal_details.append(f"WMA相对差值温和下降({wmadiff_5_20_pct:+.2f}%)(-0.5)")
            
            # 🆕 短期WMA差值信号 (WMA3-5)
            wmadiff_3_5 = wma_results.get('WMA_DIFF_3_5')
            if wmadiff_3_5 is not None:
                if wmadiff_3_5 > 0.002:  # 超短期差值为正，短期加速
                    signal_score += 0.5
                    signal_details.append(f"超短期WMA加速上升({wmadiff_3_5:+.4f})(+0.5)")
                elif wmadiff_3_5 < -0.002:  # 超短期差值为负，短期减速
                    signal_score -= 0.5
                    signal_details.append(f"超短期WMA加速下降({wmadiff_3_5:+.4f})(-0.5)")
            
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