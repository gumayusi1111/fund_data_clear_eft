#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA结果处理器模块
================

专门负责WMA计算结果的格式化、保存和展示
"""

import os
import json
import csv
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from .config import WMAConfig


def convert_numpy_types(obj):
    """
    转换numpy类型为Python原生类型，用于JSON序列化
    
    🔬 科学序列化: 处理所有numpy类型，确保JSON兼容性
    """
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    return obj


class ResultProcessor:
    """WMA结果处理器"""
    
    def __init__(self, config: WMAConfig):
        """
        初始化结果处理器
        
        Args:
            config: WMA配置对象
        """
        self.config = config
        print("💾 结果处理器初始化完成")
    
    def format_single_result(self, etf_code: str, wma_results: Dict, latest_price: Dict, 
                           date_range: Dict, data_optimization: Dict, signals: Dict,
                           wma_statistics: Dict = None, quality_metrics: Dict = None) -> Dict:
        """
        格式化单个ETF的计算结果
        
        Args:
            etf_code: ETF代码
            wma_results: WMA计算结果
            latest_price: 最新价格信息
            date_range: 日期范围
            data_optimization: 数据优化信息
            signals: 信号分析结果
            wma_statistics: WMA统计信息（可选）
            quality_metrics: 质量指标（可选）
            
        Returns:
            Dict: 格式化后的结果
        """
        result = {
            'etf_code': etf_code,
            'adj_type': self.config.adj_type,
            'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_optimization': data_optimization,
            'data_range': date_range,
            'latest_price': latest_price,
            'wma_values': wma_results,
            'signals': signals
        }
        
        # 添加可选的统计信息
        if wma_statistics:
            result['wma_statistics'] = wma_statistics
        
        if quality_metrics:
            result['quality_metrics'] = quality_metrics
        
        return result
    
    def save_results(self, results_list: List[Dict], output_dir: str = "data") -> Dict[str, str]:
        """
        保存精简计算结果 - 只输出CSV格式
        
        Args:
            results_list: 计算结果列表
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 保存的文件路径
            
        🔬 科学文件格式:
        - CSV: 表格化WMA数据，便于Excel分析和数据处理
        """
        if not results_list:
            print("❌ 没有有效结果可保存")
            return {}
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 🔬 保存CSV结果文件 (表格化数据)
        csv_file = os.path.join(output_dir, f"WMA_Results_{timestamp}.csv")
        self._create_csv_file(results_list, csv_file)
        
        # 计算文件大小
        csv_size = os.path.getsize(csv_file)
        
        print(f"💾 结果文件已保存:")
        print(f"   📈 CSV数据: {os.path.basename(csv_file)} ({csv_size} 字节)")
        print(f"   💿 总大小: {csv_size / 1024:.1f} KB")
        
        return {
            'csv_file': csv_file
        }
    
    def _create_csv_file(self, results_list: List[Dict], csv_file: str):
        """
        创建CSV文件 - 科学数据表格
        
        Args:
            results_list: 结果列表
            csv_file: CSV文件路径
            
        🔬 CSV结构:
        - ETF基本信息: 代码、复权类型、日期、价格
        - WMA指标: 各周期WMA值
        - 技术分析: 多空排列、趋势分析
        - 交易信号: 买卖建议、置信度
        """
        try:
            # 准备CSV数据
            csv_data = []
            
            for result in results_list:
                # 🔬 精简CSV - 只保留最重要的核心字段
                row = {
                    'ETF代码': result['etf_code'],
                    '复权类型': result['adj_type'],
                    '最新日期': result['latest_price']['date'],
                    '最新价格': result['latest_price']['close'],
                    '涨跌幅(%)': result['latest_price']['change_pct'],
                }
                
                # WMA核心指标
                wma_values = result['wma_values']
                for period in self.config.wma_periods:
                    wma_key = f'WMA_{period}'
                    wma_val = wma_values.get(wma_key)
                    row[f'WMA{period}'] = round(wma_val, 6) if wma_val is not None else ''
                
                # 重要信号
                signals = result['signals']
                row['多空排列'] = signals.get('alignment', '')
                
                # 🔬 高级分析字段（仅在开启时显示）
                if 'trading_signals' in signals:
                    trading_signals = signals['trading_signals']
                    row['交易信号'] = trading_signals.get('primary_signal', '')
                    row['信号强度'] = trading_signals.get('signal_strength', '')
                    row['置信度(%)'] = trading_signals.get('confidence_level', '')
                
                csv_data.append(row)
            
            # 写入CSV文件
            if csv_data:
                with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
                
                print(f"   📈 CSV结构: {len(csv_data)}行 × {len(csv_data[0])}列")
            
        except Exception as e:
            print(f"❌ CSV文件创建失败: {e}")
    
    def create_summary_data(self, results_list: List[Dict]) -> Dict:
        """创建汇总数据"""
        return {
            'calculation_summary': {
                'total_etfs': len(results_list),
                'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'adj_type': self.config.adj_type,
                'wma_periods': self.config.wma_periods,
                'optimization': f'只读取最新{self.config.required_rows}行数据',
                'data_source': f'ETF日更/{self.config.get_adj_folder_name()}'
            },
            'results': results_list
        }
    
    def _create_readable_summary(self, results_list: List[Dict], summary_data: Dict, summary_file: str):
        """创建可读的摘要文件"""
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("🚀 WMA计算结果摘要\n")
            f.write("=" * 60 + "\n\n")
            
            # 写入汇总信息
            calc_summary = summary_data['calculation_summary']
            f.write(f"📊 计算汇总:\n")
            f.write(f"   ETF数量: {calc_summary['total_etfs']}\n")
            f.write(f"   复权类型: {calc_summary['adj_type']}\n")
            f.write(f"   计算时间: {calc_summary['calculation_time']}\n")
            f.write(f"   数据优化: {calc_summary['optimization']}\n\n")
            
            # 写入个别ETF结果
            for i, result in enumerate(results_list, 1):
                f.write(f"{i}. 📈 {result['etf_code']}\n")
                f.write(f"   📅 最新日期: {result['latest_price']['date']}\n")
                f.write(f"   💰 最新价格: {result['latest_price']['close']:.3f}\n")
                f.write(f"   📈 涨跌幅: {result['latest_price']['change_pct']:+.3f}%\n\n")
                
                f.write("   🎯 WMA指标:\n")
                for period in self.config.wma_periods:
                    wma_val = result['wma_values'].get(f'WMA_{period}')
                    if wma_val:
                        f.write(f"      WMA{period}: {wma_val:.6f}\n")
                
                f.write(f"\n   🔄 多空排列: {result['signals']['alignment']}\n")
                f.write("-" * 40 + "\n\n")
    
    def display_results(self, results_list: List[Dict]):
        """显示计算结果摘要"""
        if not results_list:
            print("❌ 没有有效结果可显示")
            return
        
        print(f"\n📊 WMA计算结果摘要 ({len(results_list)}个ETF)")
        print("=" * 80)
        
        for i, result in enumerate(results_list, 1):
            print(f"\n{i}. 📈 {result['etf_code']} ({result['adj_type']})")
            print(f"   📅 日期: {result['latest_price']['date']}")
            print(f"   💰 价格: {result['latest_price']['close']:.3f} ({result['latest_price']['change_pct']:+.3f}%)")
            
            print(f"   🎯 WMA值:", end="")
            for period in self.config.wma_periods:
                wma_val = result['wma_values'].get(f'WMA_{period}')
                if wma_val:
                    print(f" WMA{period}:{wma_val:.3f}", end="")
            print()
            
            print(f"   🔄 排列: {result['signals']['alignment']}")
    
    def get_result_stats(self, results_list: List[Dict]) -> Dict:
        """获取结果统计信息"""
        if not results_list:
            return {}
        
        return {
            'total_etfs': len(results_list),
            'successful_calculations': len(results_list)
        } 