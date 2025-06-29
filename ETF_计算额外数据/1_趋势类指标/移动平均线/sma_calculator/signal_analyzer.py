#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA信号分析器模块 - 科学改进版
============================

基于学术研究的科学SMA多空排列算法
采用统计显著性阈值和相对差距分析
"""

from typing import Dict, Optional, Tuple
from .config import SMAConfig


class SignalAnalyzer:
    """SMA信号分析器 - 科学改进版"""
    
    def __init__(self, config: SMAConfig):
        """
        初始化信号分析器
        
        Args:
            config: SMA配置对象
        """
        self.config = config
        
        # 🎯 使用SMA系统专属参数（标准基准系统）
        self.thresholds = config.get_system_thresholds()
        self.score_weights = config.get_system_score_weights()
        self.volume_threshold = config.get_volume_threshold()
        self.tolerance_ratio = config.get_tolerance_ratio()
        
        print("📊 SMA信号分析器初始化完成 (系统差异化版)")
        print(f"🎯 SMA专属阈值: {self.thresholds}")
        print(f"📊 SMA专属权重: {self.score_weights}")
        print(f"📈 量能阈值: {self.volume_threshold}, 容错率: {self.tolerance_ratio}")
    
    def _calculate_relative_gap(self, ma_short: float, ma_long: float) -> float:
        """
        计算相对差距百分比
        
        Args:
            ma_short: 短期移动平均线
            ma_long: 长期移动平均线
            
        Returns:
            float: 相对差距百分比
        """
        if ma_long <= 0:
            return 0.0
        return ((ma_short - ma_long) / ma_long) * 100
    
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
    
    def _scientific_alignment_analysis(self, sma5: float, sma10: float, 
                                     sma20: float, sma60: Optional[float] = None) -> Tuple[str, float, Dict]:
        """
        科学的多空排列分析 - 使用SMA系统专属参数
        
        Args:
            sma5: 5日移动平均线
            sma10: 10日移动平均线
            sma20: 20日移动平均线
            sma60: 60日移动平均线（可选）
            
        Returns:
            Tuple[str, float, Dict]: (排列状态, 评分, 详细分析)
        """
        details = {
            'gap_5_10_pct': 0.0,
            'gap_10_20_pct': 0.0,
            'gap_20_60_pct': 0.0,
            'avg_gap_pct': 0.0,
            'min_gap_pct': 0.0,
            'statistical_significance': False,
            'strength_level': '微弱',
            'direction': '震荡',
            'scientific_basis': f'基于SMA系统专属参数 (标准基准{self.thresholds["minimal"]}%)',
            'system_type': 'SMA (标准基准)'
        }
        
        # 计算相对差距
        gap_5_10 = self._calculate_relative_gap(sma5, sma10)
        gap_10_20 = self._calculate_relative_gap(sma10, sma20)
        details['gap_5_10_pct'] = gap_5_10
        details['gap_10_20_pct'] = gap_10_20
        
        if sma60 is not None:
            gap_20_60 = self._calculate_relative_gap(sma20, sma60)
            details['gap_20_60_pct'] = gap_20_60
        
        # 统计显著性检验
        primary_gaps = [gap_5_10, gap_10_20]
        avg_gap = sum([abs(gap) for gap in primary_gaps]) / len(primary_gaps)
        min_gap = min([abs(gap) for gap in primary_gaps])
        
        details['avg_gap_pct'] = avg_gap
        details['min_gap_pct'] = min_gap
        
        # 🔬 核心：统计显著性检验（使用SMA系统专属阈值）
        if min_gap < self.thresholds['noise_filter']:
            # 差距太小，视为市场噪音
            details['statistical_significance'] = False
            return "震荡排列", 0.0, details
        
        details['statistical_significance'] = True
        
        # 方向一致性检验（使用SMA系统专属阈值）
        if gap_5_10 > self.thresholds['minimal'] and gap_10_20 > self.thresholds['minimal']:
            # 多头排列
            direction = '多头'
            strength = self._classify_strength(avg_gap)
            
            # 长期趋势确认（如果有60日MA）
            if sma60 is not None and gap_20_60 > self.thresholds['minimal']:
                status = f"长期{strength}多头排列"
                score_multiplier = 1.2  # 长期趋势确认加成
            else:
                status = f"{strength}多头排列"
                score_multiplier = 1.0
            
            base_score = self.score_weights[strength]
            final_score = base_score * score_multiplier
            
        elif gap_5_10 < -self.thresholds['minimal'] and gap_10_20 < -self.thresholds['minimal']:
            # 空头排列
            direction = '空头'
            strength = self._classify_strength(avg_gap)
            
            # 长期趋势确认（如果有60日MA）
            if sma60 is not None and gap_20_60 < -self.thresholds['minimal']:
                status = f"长期{strength}空头排列"
                score_multiplier = 1.2  # 长期趋势确认加成
            else:
                status = f"{strength}空头排列"
                score_multiplier = 1.0
            
            base_score = self.score_weights[strength]
            final_score = -base_score * score_multiplier  # 空头为负分
            
        else:
            # 方向不一致，视为震荡
            direction = '震荡'
            status = "方向分化"
            final_score = 0.0
            strength = "微弱"
        
        # 质量评估：对差距过小的情况进行惩罚，对差距明显的情况给予奖励
        if avg_gap < self.thresholds['minimal']:
            final_score *= 0.5  # 差距过小，信号质量折扣
        elif avg_gap > 2.0:
            final_score *= 1.1  # 差距明显，信号质量提升
        
        details['strength_level'] = strength
        details['direction'] = direction
        
        return status, round(final_score, 2), details
    
    def calculate_alignment(self, sma_results: Dict[str, Optional[float]]) -> Dict:
        """
        计算多空排列状态 - 科学改进版
        
        Args:
            sma_results: SMA计算结果
            
        Returns:
            Dict: 包含详细分析的排列结果
        """
        try:
            sma5 = sma_results.get('SMA_5')
            sma10 = sma_results.get('SMA_10')
            sma20 = sma_results.get('SMA_20')
            sma60 = sma_results.get('SMA_60')
            
            # 确保至少有核心的SMA值
            if any(sma is None for sma in [sma5, sma10, sma20]):
                return {
                    'status': '数据不足',
                    'score': 0.0,
                    'strength_level': '未知',
                    'details': {'error': '缺少必要的SMA数据'}
                }
            
            # 🔬 科学分析
            status, score, details = self._scientific_alignment_analysis(sma5, sma10, sma20, sma60)
            
            return {
                'status': status,
                'score': score,
                'strength_level': details['strength_level'],
                'details': details
            }
            
        except Exception as e:
            print(f"❌ SMA多空排列计算失败: {e}")
            return {
                'status': '计算失败',
                'score': 0.0,
                'strength_level': '未知',
                'details': {'error': str(e)}
            }
    
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