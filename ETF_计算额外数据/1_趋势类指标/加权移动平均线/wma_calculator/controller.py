#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA主控制器模块
==============

整合所有组件，提供统一的WMA计算接口
"""

from typing import List, Optional, Dict, Any
from .config import WMAConfig
from .data_reader import ETFDataReader
from .wma_engine import WMAEngine
from .signal_analyzer import SignalAnalyzer
from .file_manager import FileManager
import os
from datetime import datetime


class WMAController:
    """WMA主控制器"""
    
    def __init__(self, adj_type: str = "前复权", wma_periods: Optional[List[int]] = None, 
                 output_dir: Optional[str] = None):
        """
        初始化WMA控制器
        
        Args:
            adj_type: 复权类型
            wma_periods: WMA周期列表
            output_dir: 输出目录（None时使用配置中的智能路径）
        """
        print("🚀 WMA控制器初始化...")
        print("=" * 60)
        
        # 初始化配置
        self.config = WMAConfig(adj_type, wma_periods)
        
        # 验证数据路径
        if not self.config.validate_data_path():
            raise ValueError("数据路径验证失败")
        
        # 🔬 智能输出目录设置
        if output_dir is None:
            output_dir = self.config.default_output_dir
        
        # 初始化各个组件
        self.data_reader = ETFDataReader(self.config)
        self.wma_engine = WMAEngine(self.config)
        self.signal_analyzer = SignalAnalyzer(self.config)
        self.file_manager = FileManager(output_dir)
        
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
        处理单个ETF的WMA计算
        
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
            
            # 步骤2: 计算WMA
            wma_results = self.wma_engine.calculate_all_wma(df)
            if not wma_results or all(v is None for v in wma_results.values()):
                print(f"❌ {etf_code} WMA计算失败")
                return None
            
            # 步骤3: 获取价格和日期信息
            latest_price = self.data_reader.get_latest_price_info(df)
            date_range = self.data_reader.get_date_range(df)
            
            # 步骤4: 信号分析
            alignment = self.signal_analyzer.calculate_alignment(wma_results)
            price_signals = self.signal_analyzer.calculate_price_signals(
                latest_price['close'], wma_results
            )
            
            signals = {
                'alignment': alignment,
                'price_vs_wma': price_signals
            }
            
            # 步骤5: 高级分析（可选）
            wma_statistics = None
            quality_metrics = None
            
            if include_advanced_analysis:
                wma_statistics = self.wma_engine.calculate_wma_statistics(df, wma_results)
                quality_metrics = self.wma_engine.get_wma_quality_metrics(df, wma_results)
                
                # 趋势分析
                trend_analysis = self.signal_analyzer.analyze_trend_signals(wma_results)
                
                # 交易信号
                trading_signals = self.signal_analyzer.generate_trading_signals(
                    latest_price['close'], wma_results, alignment, trend_analysis
                )
                
                signals.update({
                    'trend_analysis': trend_analysis,
                    'trading_signals': trading_signals
                })
            
            # 步骤6: 数据优化信息
            data_optimization = {
                'total_available_days': total_rows,
                'used_days': len(df),
                'efficiency_gain': f"{((total_rows - len(df)) / total_rows * 100):.1f}%" if total_rows > len(df) else "0.0%"
            }
            
            # 步骤7: 格式化结果
            from .result_processor import ResultProcessor
            result_processor = ResultProcessor(self.config)
            
            result = result_processor.format_single_result(
                etf_code, wma_results, latest_price, date_range, 
                data_optimization, signals, wma_statistics, quality_metrics
            )
            
            # 步骤8: 清理内存
            self.data_reader.cleanup_memory(df)
            
            print(f"✅ {etf_code} 处理完成")
            return result
            
        except Exception as e:
            print(f"❌ {etf_code} 处理失败: {e}")
            return None
    
    def process_multiple_etfs(self, etf_codes: List[str], 
                            include_advanced_analysis: bool = False) -> List[Dict]:
        """
        处理多个ETF的WMA计算
        
        Args:
            etf_codes: ETF代码列表
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            List[Dict]: 计算结果列表
        """
        results = []
        success_count = 0
        
        print(f"📊 开始批量处理 {len(etf_codes)} 个ETF...")
        
        for i, etf_code in enumerate(etf_codes, 1):
            print(f"\n{'='*60}")
            print(f"🔄 处理进度: {i}/{len(etf_codes)} - {etf_code}")
            print(f"{'='*60}")
            
            result = self.process_single_etf(etf_code, include_advanced_analysis)
            
            if result:
                results.append(result)
                success_count += 1
            else:
                print(f"❌ {etf_code} 处理失败，跳过...")
        
        print(f"\n✅ 批量处理完成! 成功处理 {success_count}/{len(etf_codes)} 个ETF")
        return results
    
    def calculate_and_save(self, etf_codes: List[str], output_dir: Optional[str] = None,
                          include_advanced_analysis: bool = False) -> Dict[str, Any]:
        """
        计算并保存结果的完整流程
        
        Args:
            etf_codes: ETF代码列表
            output_dir: 输出目录（可选）
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            Dict[str, Any]: 处理结果摘要
        """
        # 处理ETF
        results = self.process_multiple_etfs(etf_codes, include_advanced_analysis)
        
        if not results:
            print("❌ 没有成功处理的ETF")
            return {'success': False, 'message': '没有成功处理的ETF'}
        
        # 保存结果
        from .result_processor import ResultProcessor
        result_processor = ResultProcessor(self.config)
        
        # 🔬 智能输出目录处理
        if output_dir:
            output_dir = self.file_manager.create_output_directory(output_dir)
        else:
            # 使用配置中的智能路径
            output_dir = self.file_manager.create_output_directory(self.config.default_output_dir)
        
        saved_files = result_processor.save_results(results, output_dir)
        
        # 显示结果
        result_processor.display_results(results)
        
        # 显示文件摘要
        self.file_manager.show_output_summary(output_dir)
        
        # 获取结果统计
        stats = result_processor.get_result_stats(results)
        
        return {
            'success': True,
            'processed_etfs': len(results),
            'total_etfs': len(etf_codes),
            'success_rate': len(results) / len(etf_codes) * 100,
            'output_directory': output_dir,
            'saved_files': saved_files,
            'statistics': stats
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
            wma_values = result['wma_values']
            signals = result['signals']
            
            print(f"\n📊 {etf_code} 快速分析结果:")
            print(f"   💰 价格: {latest['close']:.3f} ({latest['change_pct']:+.3f}%)")
            print(f"   🎯 WMA: ", end="")
            for period in self.config.wma_periods:
                wma_val = wma_values.get(f'WMA_{period}')
                if wma_val:
                    print(f"WMA{period}:{wma_val:.3f} ", end="")
            print()
            
            # 🆕 显示WMA差值信息
            wmadiff_5_20 = wma_values.get('WMA_DIFF_5_20')
            wmadiff_5_20_pct = wma_values.get('WMA_DIFF_5_20_PCT')
            wmadiff_3_5 = wma_values.get('WMA_DIFF_3_5')
            
            if wmadiff_5_20 is not None:
                trend_icon = "📈" if wmadiff_5_20 > 0 else ("📉" if wmadiff_5_20 < 0 else "➡️")
                print(f"   📊 WMA差值: 5-20={wmadiff_5_20:+.6f} ({wmadiff_5_20_pct:+.2f}%) {trend_icon}")
                
                if wmadiff_3_5 is not None:
                    print(f"              3-5={wmadiff_3_5:+.6f} (超短期动量)")
            
            # 🔬 显示科学的排列分析结果
            alignment = signals['alignment']
            if isinstance(alignment, dict):
                status = alignment.get('status', '未知')
                score = alignment.get('score', 0)
                strength = alignment.get('strength_level', '未知')
                print(f"   🔄 排列: {status} (评分:{score:+.2f}, 强度:{strength})")
                
                # 显示详细差距信息
                if 'details' in alignment and isinstance(alignment['details'], dict):
                    details = alignment['details']
                    avg_diff = details.get('avg_diff_pct', 0)
                    min_diff = details.get('min_diff_pct', 0)
                    print(f"        差距分析: 平均{avg_diff:.2f}%, 最小{min_diff:.2f}%")
            else:
                print(f"   🔄 排列: {alignment}")
            
            if 'trading_signals' in signals:
                trading = signals['trading_signals']
                print(f"   🎯 信号: {trading['primary_signal']} (强度:{trading['signal_strength']}, 置信度:{trading['confidence_level']:.0f}%)")
        
        return result 
    
    def process_screening_results(self, thresholds: List[str] = None, 
                                include_advanced_analysis: bool = False) -> Dict[str, List[Dict]]:
        """
        处理ETF筛选结果的WMA计算
        
        Args:
            thresholds: 门槛列表，默认为 ["3000万门槛", "5000万门槛"]
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            Dict[str, List[Dict]]: 各门槛的计算结果 {threshold: [results_list]}
            
        🔬 新功能: 基于ETF初筛结果进行批量WMA计算
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
            results = self.process_multiple_etfs(etf_codes, include_advanced_analysis)
            screening_results[threshold] = results
            
            print(f"✅ {threshold}: 成功计算 {len(results)}/{len(etf_codes)} 个ETF")
        
        return screening_results
    
    def calculate_and_save_screening_results(self, thresholds: List[str] = None, 
                                           output_dir: Optional[str] = None,
                                           include_advanced_analysis: bool = False) -> Dict[str, Any]:
        """
        计算并保存基于筛选结果的WMA数据 - 只保存ETF完整历史数据文件
        
        Args:
            thresholds: 门槛列表
            output_dir: 输出目录（可选）
            include_advanced_analysis: 是否包含高级分析
            
        Returns:
            Dict[str, Any]: 处理结果摘要
            
        🔬 完整流程: 筛选结果读取 → WMA计算 → 完整历史数据文件生成（按时间倒序）
        """
        print("🚀 开始基于ETF筛选结果的WMA批量计算...")
        
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
        
        # 保存结果 - 只保存ETF历史数据文件
        from .result_processor import ResultProcessor
        result_processor = ResultProcessor(self.config)
        
        # 保存筛选批量结果（每个ETF一个完整历史数据文件）
        save_stats = result_processor.save_screening_batch_results(screening_results, output_dir)
        
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
    
    def _save_screening_summary_csv(self, screening_results: Dict, output_dir: str):
        """保存筛选结果汇总CSV - 已移除此功能"""
        # 🔬 功能移除：不再生成汇总CSV文件，用户只需要ETF历史数据文件
        pass
    
    def _display_screening_results_summary(self, screening_results: Dict):
        """显示筛选结果摘要"""
        print(f"\n📊 ETF筛选结果WMA计算摘要")
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
                wma_values = result['wma_values']
                
                print(f"   {i}. {result['etf_code']}: 最新价格{latest['close']:.3f} ", end="")
                
                # 显示主要WMA值
                for period in [5, 20]:  # 显示核心周期
                    wma_val = wma_values.get(f'WMA_{period}')
                    if wma_val:
                        print(f"WMA{period}:{wma_val:.3f} ", end="")
                
                # 显示WMA差值
                wmadiff_5_20 = wma_values.get('WMA_DIFF_5_20')
                if wmadiff_5_20 is not None:
                    trend_icon = "📈" if wmadiff_5_20 > 0 else "📉" 
                    print(f"差值:{wmadiff_5_20:+.4f} {trend_icon}")
                else:
                    print()
            
            if len(results_list) > 5:
                print(f"   ... 还有 {len(results_list) - 5} 个ETF")
        
        total_etfs = sum(len(results) for results in screening_results.values())
        print(f"\n🎯 总计: {total_etfs} 个ETF，每个都包含完整历史WMA数据（按时间倒序）") 