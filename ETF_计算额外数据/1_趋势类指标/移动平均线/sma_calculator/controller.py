#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA主控制器模块 - 中短线专版
=========================

整合所有组件，提供统一的SMA计算接口
支持单个ETF计算、批量处理和筛选结果处理
"""

from typing import List, Optional, Dict, Any
from .config import SMAConfig
from .data_reader import ETFDataReader
from .sma_engine import SMAEngine
# from .signal_analyzer import SignalAnalyzer  # 🚫 已移除复杂分析
from .result_processor import ResultProcessor
from .file_manager import FileManager
import os
from datetime import datetime


class SMAController:
    """SMA主控制器 - 中短线专版"""
    
    def __init__(self, adj_type: str = "前复权", sma_periods: Optional[List[int]] = None, 
                 output_dir: Optional[str] = None):
        """
        初始化SMA控制器
        
        Args:
            adj_type: 复权类型
            sma_periods: SMA周期列表
            output_dir: 输出目录（None时使用配置中的智能路径）
        """
        print("🚀 SMA控制器初始化... (中短线专版)")
        print("=" * 60)
        
        # 初始化配置
        self.config = SMAConfig(adj_type, sma_periods)
        
        # 验证数据路径
        if not self.config.validate_data_path():
            raise ValueError("数据路径验证失败")
        
        # 🔬 智能输出目录设置
        if output_dir is None:
            output_dir = self.config.default_output_dir
        
        # 初始化各个组件
        self.data_reader = ETFDataReader(self.config)
        self.sma_engine = SMAEngine(self.config)
        # self.signal_analyzer = SignalAnalyzer(self.config)  # 🚫 已移除复杂分析
        self.file_manager = FileManager(output_dir)
        self.result_processor = ResultProcessor(self.config, self.file_manager)
        
        print("✅ 所有组件初始化完成")
        print("=" * 60)
    
    def get_available_etfs(self) -> List[str]:
        """
        获取可用的ETF代码列表
        
        Returns:
            List[str]: 可用的ETF代码列表
        """
        return self.data_reader.get_available_etfs()
    
    def process_single_etf(self, etf_code: str, include_advanced_analysis: bool = False) -> Optional[Dict]:
        """
        处理单个ETF的SMA计算
        
        Args:
            etf_code: ETF代码
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            Dict: 计算结果或None
        """
        print(f"🔄 开始处理: {etf_code}")
        
        try:
            # 步骤1: 读取数据
            data_result = self.data_reader.read_etf_data(etf_code)
            if data_result is None:
                print(f"❌ {etf_code} 数据读取失败")
                return None
            
            df, total_rows = data_result
            
            # 步骤2: 计算SMA
            sma_results = self.sma_engine.calculate_all_sma(df)
            if not sma_results or all(v is None for v in sma_results.values()):
                print(f"❌ {etf_code} SMA计算失败")
                return None
            
            # 步骤3: 获取价格和日期信息
            latest_price = self.data_reader.get_latest_price_info(df)
            date_range = self.data_reader.get_date_range(df)
            
            # 步骤4: 🚫 简化信号分析 - 只保留基础数据
            signals = {
                'status': 'simplified'  # 标记为简化模式
            }
            
            # 步骤6: 高级分析（可选）
            sma_statistics = None
            quality_metrics = None
            if include_advanced_analysis:
                # 这里可以添加更多的高级分析
                quality_metrics = self.sma_engine.get_sma_quality_metrics(df, sma_results)
            
            # 构建完整结果
            result = {
                'etf_code': etf_code,
                'adj_type': self.config.adj_type,
                'latest_price': latest_price,
                'date_range': date_range,
                'data_info': {
                    'total_rows': total_rows,
                    'used_rows': len(df),
                    'data_efficiency': round((len(df) / total_rows) * 100, 2)
                },
                'sma_values': sma_results,
                'signals': signals,
                'processing_time': datetime.now().isoformat()
            }
            
            if include_advanced_analysis:
                result['advanced_analysis'] = {
                    'quality_metrics': quality_metrics
                }
            
            print(f"✅ {etf_code} 处理完成")
            return result
            
        except Exception as e:
            print(f"❌ {etf_code} 处理异常: {str(e)}")
            return None
    
    def process_screening_results(self, thresholds: List[str] = None, 
                                include_advanced_analysis: bool = False) -> Dict[str, List[Dict]]:
        """
        处理ETF筛选结果的SMA计算 - 模仿WMA的多门槛支持
        
        Args:
            thresholds: 门槛列表，默认为 ["3000万门槛", "5000万门槛"]
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            Dict[str, List[Dict]]: 各门槛的计算结果 {threshold: [results_list]}
            
        🔬 新功能: 基于ETF初筛结果进行批量SMA计算
        """
        if thresholds is None:
            thresholds = ["3000万门槛", "5000万门槛"]
        
        screening_results = {}
        
        for threshold in thresholds:
            print(f"\n{'='*60}")
            print(f"🔄 处理{threshold}筛选结果")
            print(f"{'='*60}")
            
            # 获取筛选通过的ETF代码
            etf_codes = self.data_reader.get_screening_etf_codes(threshold)
            
            if not etf_codes:
                print(f"❌ {threshold}: 没有找到筛选结果")
                screening_results[threshold] = []
                continue
            
            print(f"📊 {threshold}: 找到 {len(etf_codes)} 个通过筛选的ETF")
            
            # 批量处理这些ETF
            results = []
            success_count = 0
            failed_count = 0
            
            for i, etf_code in enumerate(etf_codes, 1):
                print(f"\n🔄 处理进度: {i}/{len(etf_codes)} - {etf_code}")
                
                result = self.process_single_etf(etf_code, include_advanced_analysis)
                
                if result:
                    results.append(result)
                    success_count += 1
                else:
                    failed_count += 1
                
                # 每处理10个显示一次进度
                if i % 10 == 0:
                    progress = (i / len(etf_codes)) * 100
                    print(f"📈 处理进度: {progress:.1f}% (成功:{success_count}, 失败:{failed_count})")
            
            screening_results[threshold] = results
            print(f"✅ {threshold}: 成功计算 {len(results)}/{len(etf_codes)} 个ETF")
        
        return screening_results
    
    def calculate_and_save_screening_results(self, thresholds: List[str] = None, 
                                           output_dir: Optional[str] = None,
                                           include_advanced_analysis: bool = False) -> Dict[str, Any]:
        """
        计算并保存基于筛选结果的SMA数据 - 模仿WMA的完整流程
        
        Args:
            thresholds: 门槛列表，默认为 ["3000万门槛", "5000万门槛"]
            output_dir: 输出目录（可选）
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            Dict[str, Any]: 处理结果摘要
            
        🔬 完整流程: 筛选结果读取 → SMA计算 → 完整历史数据文件生成（按时间倒序）
        """
        print("🚀 开始基于ETF筛选结果的SMA批量计算...")
        
        # 处理筛选结果
        screening_results = self.process_screening_results(thresholds, include_advanced_analysis)
        
        if not any(results for results in screening_results.values()):
            print("❌ 没有成功处理的筛选结果")
            return {'success': False, 'message': '没有成功处理的筛选结果'}
        
        # 🔬 智能输出目录处理
        if output_dir:
            output_dir = self.file_manager.create_output_directory(output_dir)
        else:
            # 使用配置中的智能路径
            output_dir = self.file_manager.create_output_directory(self.config.default_output_dir)
        
        # 保存结果 - 保存ETF历史数据文件
        save_stats = self.result_processor.save_screening_batch_results(screening_results, output_dir)
        
        # 显示结果摘要
        self._display_screening_results_summary(screening_results)
        
        # 显示文件摘要
        self.file_manager.show_output_summary(output_dir)
        
        # 计算整体统计
        total_etfs = sum(len(results) for results in screening_results.values())
        total_thresholds = len([t for t in screening_results if screening_results[t]])
        
        return {
            'success': True,
            'total_etfs_processed': total_etfs,
            'thresholds_processed': total_thresholds,
            'output_directory': output_dir,
            'save_statistics': save_stats,
            'screening_results': screening_results
        }
    
    def quick_analysis(self, etf_code: str) -> Optional[Dict]:
        """
        快速分析单个ETF（不保存文件）
        
        Args:
            etf_code: ETF代码
            
        Returns:
            Dict: 分析结果或None
        """
        print(f"⚡ 快速分析: {etf_code}")
        result = self.process_single_etf(etf_code, include_advanced_analysis=True)
        
        if result:
            # 显示关键信息
            latest = result['latest_price']
            sma_values = result['sma_values']
            signals = result['signals']
            
            print(f"\n📊 {etf_code} 快速分析结果:")
            print(f"   💰 价格: {latest['close']:.3f} ({latest['change_pct']:+.3f}%)")
            print(f"   🎯 SMA: ", end="")
            for period in self.config.sma_periods:
                sma_val = sma_values.get(f'SMA_{period}')
                if sma_val:
                    print(f"MA{period}:{sma_val:.3f} ", end="")
            print()
            
            # 显示SMA差值信息
            smadiff_5_20 = sma_values.get('SMA_DIFF_5_20')
            smadiff_5_20_pct = sma_values.get('SMA_DIFF_5_20_PCT')
            smadiff_5_10 = sma_values.get('SMA_DIFF_5_10')
            
            if smadiff_5_20 is not None:
                trend_icon = "📈" if smadiff_5_20 > 0 else ("📉" if smadiff_5_20 < 0 else "➡️")
                print(f"   📊 SMA差值: 5-20={smadiff_5_20:+.6f} ({smadiff_5_20_pct:+.2f}%) {trend_icon}")
                
                if smadiff_5_10 is not None:
                    print(f"              5-10={smadiff_5_10:+.6f} (短期动量)")
            
            # 🚫 已移除复杂排列和信号分析 - 只保留数据计算
        
        return result
    
    def _display_screening_results_summary(self, screening_results: Dict):
        """显示筛选结果摘要 - 模仿WMA的实现"""
        print(f"\n📊 ETF筛选结果SMA计算摘要")
        print("=" * 80)
        
        for threshold, results_list in screening_results.items():
            if not results_list:
                print(f"\n❌ {threshold}: 无有效结果")
                continue
                
            print(f"\n✅ {threshold}: {len(results_list)} 个ETF完整历史数据文件")
            
            # 显示前5个代表性结果
            print(f"   🎯 代表性ETF结果:")
            for i, result in enumerate(results_list[:5], 1):
                latest = result['latest_price']
                sma_values = result['sma_values']
                
                print(f"   {i}. {result['etf_code']}: 最新价格{latest['close']:.3f} ", end="")
                
                # 显示主要SMA值
                for period in [5, 20]:  # 显示核心周期
                    sma_val = sma_values.get(f'SMA_{period}')
                    if sma_val:
                        print(f"MA{period}:{sma_val:.3f} ", end="")
                
                # 显示SMA差值
                smadiff_5_20 = sma_values.get('SMA_DIFF_5_20')
                if smadiff_5_20 is not None:
                    trend_icon = "📈" if smadiff_5_20 > 0 else "📉" 
                    print(f"差值:{smadiff_5_20:+.4f} {trend_icon}")
                else:
                    print()
            
            if len(results_list) > 5:
                print(f"   ... 还有 {len(results_list) - 5} 个ETF")
        
        total_etfs = sum(len(results) for results in screening_results.values())
        print(f"\n🎯 总计: {total_etfs} 个ETF，每个都包含完整历史SMA数据（按时间倒序）")
    
    def get_system_status(self) -> Dict:
        """
        获取系统状态信息
        
        Returns:
            Dict: 系统状态
        """
        try:
            available_etfs = self.get_available_etfs()
            
            status = {
                'system_info': {
                    'version': 'SMA Calculator v1.0 (中短线专版)',
                    'config': self.config.get_sma_display_info(),
                    'data_path': self.config.data_dir,
                    'output_path': self.file_manager.output_dir
                },
                'data_status': {
                    'available_etfs_count': len(available_etfs),
                    'data_path_valid': os.path.exists(self.config.data_dir),
                    'sample_etfs': available_etfs[:5] if available_etfs else []
                },
                'components': {
                    'data_reader': 'Ready',
                    'sma_engine': 'Ready',
                    # 'signal_analyzer': 'Ready',  # 🚫 已移除复杂分析
                    'result_processor': 'Ready',
                    'file_manager': 'Ready'
                }
            }
            
            return status
            
        except Exception as e:
            return {'error': f'获取系统状态失败: {str(e)}'}
    
    def validate_etf_code(self, etf_code: str) -> bool:
        """
        验证ETF代码是否有效
        
        Args:
            etf_code: ETF代码
            
        Returns:
            bool: 是否有效
        """
        return self.data_reader.validate_etf_code(etf_code) 