#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA结果处理器 - 中短期专版
========================

负责处理和格式化EMA计算结果
提供多种输出格式和显示选项
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .config import EMAConfig


class ResultProcessor:
    """EMA结果处理器 - 中短期专版"""
    
    def __init__(self, config: EMAConfig):
        """
        初始化结果处理器
        
        Args:
            config: EMA配置对象
        """
        self.config = config
        print("📊 EMA结果处理器初始化完成")
    
    def format_ema_result_row(self, etf_code: str, price_info: Dict, 
                             ema_values: Dict, signals: Dict) -> str:
        """
        格式化EMA结果为单行CSV格式 - 模仿SMA格式
        
        Args:
            etf_code: ETF代码
            price_info: 价格信息
            ema_values: EMA计算值
            signals: 信号分析结果
            
        Returns:
            str: CSV格式的结果行
        """
        try:
            # 基础信息
            adj_type = self.config.adj_type
            date = price_info.get('date', '')
            close = price_info.get('close', 0)
            change_pct = price_info.get('change_pct', 0)
            
            # EMA值
            ema12 = ema_values.get('ema_12', 0)
            ema26 = ema_values.get('ema_26', 0)
            
            # EMA差值指标
            ema_diff = ema_values.get('ema_diff_12_26', 0)
            ema_diff_pct = ema_values.get('ema_diff_12_26_pct', 0)
            
            # EMA排列
            arrangement = signals.get('arrangement', {}).get('arrangement', '未知排列')
            
            # 构建CSV行
            csv_row = (
                f"{etf_code},{adj_type},{date},{close},{change_pct:+.3f},"
                f"{ema12:.6f},{ema26:.6f},"
                f"{ema_diff:+.6f},{ema_diff_pct:+.3f},"
                f"{arrangement}"
            )
            
            return csv_row
            
        except Exception as e:
            print(f"⚠️  格式化结果失败: {str(e)}")
            return f"{etf_code},错误,{str(e)}"
    
    def get_csv_header(self) -> str:
        """
        获取CSV文件头部
        
        Returns:
            str: CSV头部
        """
        return "ETF代码,复权类型,最新日期,最新价格,涨跌幅(%),EMA12,EMA26,EMA差值(12-26),EMA差值(%),EMA排列"
    
    def format_console_output(self, etf_code: str, price_info: Dict,
                            ema_values: Dict, signals: Dict) -> str:
        """
        格式化控制台输出 - 模仿SMA风格
        
        Args:
            etf_code: ETF代码
            price_info: 价格信息
            ema_values: EMA计算值
            signals: 信号分析结果
            
        Returns:
            str: 格式化的控制台输出
        """
        try:
            # 基础价格信息
            date = price_info.get('date', '')
            close = price_info.get('close', 0)
            change_pct = price_info.get('change_pct', 0)
            change_sign = '+' if change_pct >= 0 else ''
            
            # EMA值
            ema12 = ema_values.get('ema_12', 0)
            ema26 = ema_values.get('ema_26', 0)
            
            # EMA差值
            ema_diff = ema_values.get('ema_diff_12_26', 0)
            ema_diff_pct = ema_values.get('ema_diff_12_26_pct', 0)
            
            # 趋势图标
            if ema_diff > 0:
                trend_icon = '📈'
                diff_sign = '+'
            elif ema_diff < 0:
                trend_icon = '📉'
                diff_sign = ''
            else:
                trend_icon = '➡️'
                diff_sign = ''
            
            # EMA排列
            arrangement = signals.get('arrangement', {}).get('arrangement', '未知排列')
            
            # 交易信号
            final_signal = signals.get('final_signal', '观望')
            total_score = signals.get('total_score', 0)
            confidence = signals.get('confidence', 0)
            
            # 构建输出
            output = f"""📊 {etf_code} EMA分析结果:
   💰 价格: {close} ({change_sign}{change_pct:.3f}%) [{date}]
   🎯 EMA: EMA12:{ema12:.6f} EMA26:{ema26:.6f}
   📊 EMA差值: {diff_sign}{ema_diff:.6f} ({ema_diff_pct:+.3f}%) {trend_icon}
   🔄 排列: {arrangement}
   🎯 信号: {final_signal} (强度:{total_score}, 置信度:{confidence}%)"""
            
            return output
            
        except Exception as e:
            print(f"⚠️  控制台输出格式化失败: {str(e)}")
            return f"❌ {etf_code}: 输出格式化错误 - {str(e)}"
    
    def create_summary_stats(self, results: List[Dict]) -> Dict:
        """
        创建批量处理的统计摘要
        
        Args:
            results: 批量处理结果列表
            
        Returns:
            Dict: 统计摘要
        """
        try:
            if not results:
                return {'total': 0, 'success': 0, 'error': 0}
            
            total_count = len(results)
            success_count = sum(1 for r in results if r.get('success', False))
            error_count = total_count - success_count
            
            # 信号统计
            signal_stats = {}
            arrangement_stats = {}
            
            for result in results:
                if result.get('success', False):
                    # 交易信号统计
                    signal = result.get('signals', {}).get('final_signal', '未知')
                    signal_stats[signal] = signal_stats.get(signal, 0) + 1
                    
                    # 排列统计
                    arrangement = result.get('signals', {}).get('arrangement', {}).get('arrangement', '未知')
                    arrangement_stats[arrangement] = arrangement_stats.get(arrangement, 0) + 1
            
            return {
                'total': total_count,
                'success': success_count,
                'error': error_count,
                'success_rate': round(success_count / total_count * 100, 1),
                'signal_distribution': signal_stats,
                'arrangement_distribution': arrangement_stats
            }
            
        except Exception as e:
            print(f"⚠️  统计摘要生成失败: {str(e)}")
            return {'total': 0, 'success': 0, 'error': 1}
    
    def format_summary_display(self, stats: Dict) -> str:
        """
        格式化统计摘要显示
        
        Args:
            stats: 统计数据
            
        Returns:
            str: 格式化的摘要显示
        """
        try:
            total = stats.get('total', 0)
            success = stats.get('success', 0)
            error = stats.get('error', 0)
            success_rate = stats.get('success_rate', 0)
            
            summary = f"""
📈 EMA批量处理摘要:
   📊 总计: {total} 个ETF
   ✅ 成功: {success} 个 ({success_rate}%)
   ❌ 失败: {error} 个
"""
            
            # 信号分布
            signal_dist = stats.get('signal_distribution', {})
            if signal_dist:
                summary += "\n   🎯 信号分布:\n"
                for signal, count in signal_dist.items():
                    percentage = round(count / success * 100, 1) if success > 0 else 0
                    summary += f"      {signal}: {count} ({percentage}%)\n"
            
            # 排列分布
            arrangement_dist = stats.get('arrangement_distribution', {})
            if arrangement_dist:
                summary += "\n   🔄 排列分布:\n"
                for arrangement, count in arrangement_dist.items():
                    percentage = round(count / success * 100, 1) if success > 0 else 0
                    summary += f"      {arrangement}: {count} ({percentage}%)\n"
            
            return summary.rstrip()
            
        except Exception as e:
            print(f"⚠️  摘要显示格式化失败: {str(e)}")
            return "❌ 摘要显示错误"
    
    def validate_result_data(self, etf_code: str, price_info: Dict,
                           ema_values: Dict, signals: Dict) -> bool:
        """
        验证结果数据的完整性
        
        Args:
            etf_code: ETF代码
            price_info: 价格信息
            ema_values: EMA计算值
            signals: 信号分析结果
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必要字段
            required_price_fields = ['date', 'close', 'change_pct']
            required_ema_fields = ['ema_12', 'ema_26']
            
            # 验证价格信息
            for field in required_price_fields:
                if field not in price_info:
                    print(f"⚠️  {etf_code}: 缺少价格字段 {field}")
                    return False
            
            # 验证EMA值
            for field in required_ema_fields:
                if field not in ema_values:
                    print(f"⚠️  {etf_code}: 缺少EMA字段 {field}")
                    return False
                
                # 检查EMA值是否为正数
                if ema_values[field] <= 0:
                    print(f"⚠️  {etf_code}: EMA值异常 {field}={ema_values[field]}")
                    return False
            
            # 验证信号数据
            if 'arrangement' not in signals:
                print(f"⚠️  {etf_code}: 缺少排列信息")
                return False
            
            print(f"✅ {etf_code}: 结果数据验证通过")
            return True
            
        except Exception as e:
            print(f"❌ {etf_code}: 结果验证失败 - {str(e)}")
            return False
    
    def export_to_dict(self, etf_code: str, price_info: Dict,
                      ema_values: Dict, signals: Dict) -> Dict:
        """
        导出为字典格式（便于JSON等格式化）
        
        Args:
            etf_code: ETF代码
            price_info: 价格信息
            ema_values: EMA计算值
            signals: 信号分析结果
            
        Returns:
            Dict: 完整的结果字典
        """
        try:
            return {
                'etf_code': etf_code,
                'config': {
                    'adj_type': self.config.adj_type,
                    'ema_periods': self.config.ema_periods
                },
                'price_info': price_info,
                'ema_values': ema_values,
                'signals': signals,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️  字典导出失败: {str(e)}")
            return {'error': str(e), 'etf_code': etf_code} 