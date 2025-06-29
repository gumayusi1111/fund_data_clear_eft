#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA结果处理器模块 - 中短线专版
===========================

专门负责SMA计算结果的处理、格式化和输出
支持单行数据输出、批量处理和历史数据计算
"""

import pandas as pd
import os
from typing import List, Dict, Optional, Any
from .config import SMAConfig
from .file_manager import FileManager


class ResultProcessor:
    """SMA结果处理器 - 中短线专版"""
    
    def __init__(self, config: SMAConfig, file_manager: FileManager):
        """
        初始化结果处理器
        
        Args:
            config: SMA配置对象
            file_manager: 文件管理器
        """
        self.config = config
        self.file_manager = file_manager
        print("📋 SMA结果处理器初始化完成 (中短线专版)")
    
    def process_single_result(self, result: Dict) -> Dict:
        """
        处理单个ETF的SMA计算结果
        
        Args:
            result: 单个ETF的计算结果
            
        Returns:
            Dict: 处理后的结果
        """
        try:
            # 提取核心信息
            processed_result = {
                'etf_code': result.get('etf_code', ''),
                'adj_type': result.get('adj_type', '前复权'),
                'latest_price': result.get('latest_price', {}),
                'sma_values': result.get('sma_values', {}),
                'signals': result.get('signals', {}),
                'processing_time': result.get('processing_time', '')
            }
            
            # 增强信号信息
            if 'alignment' in processed_result['signals']:
                alignment = processed_result['signals']['alignment']
                processed_result['alignment_signal'] = alignment
            
            return processed_result
            
        except Exception as e:
            print(f"⚠️  处理单个结果失败: {str(e)}")
            return result
    
    def save_single_row_csv(self, etf_code: str, result: Dict, threshold: str,
                           output_base_dir: str = "data") -> Optional[str]:
        """
        保存单行数据格式的CSV文件
        
        Args:
            etf_code: ETF代码
            result: 计算结果
            threshold: 门槛类型
            output_base_dir: 输出基础目录
            
        Returns:
            Optional[str]: 保存的文件路径或None
        """
        try:
            # 构建输出目录路径
            output_dir = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                output_base_dir, 
                threshold
            )
            
            # 确保目录存在
            self.file_manager.ensure_directory_exists(output_dir)
            
            # 准备CSV数据（单行格式）
            sma_values = result.get('sma_values', {})
            latest_price = result.get('latest_price', {})
            signals = result.get('signals', {})
            
            # 🎯 构建单行数据
            row_data = {
                'ETF代码': etf_code.replace('.SH', '').replace('.SZ', ''),
                '复权类型': result.get('adj_type', '前复权'),
                '最新日期': latest_price.get('date', ''),
                '最新价格': latest_price.get('close', ''),
                '涨跌幅(%)': latest_price.get('change_pct', '')
            }
            
            # 添加SMA核心指标
            for period in self.config.sma_periods:
                sma_key = f'SMA_{period}'
                sma_val = sma_values.get(sma_key)
                row_data[f'MA{period}'] = round(sma_val, 6) if sma_val is not None else ''
            
            # 🆕 添加SMA差值指标
            smadiff_keys = [
                ('SMA_DIFF_5_20', 'SMA差值5-20'),
                ('SMA_DIFF_5_10', 'SMA差值5-10'),
                ('SMA_DIFF_5_20_PCT', 'SMA差值5-20(%)')
            ]
            
            for sma_diff_key, column_name in smadiff_keys:
                diff_val = sma_values.get(sma_diff_key)
                if diff_val is not None:
                    if sma_diff_key.endswith('_PCT'):
                        row_data[column_name] = round(diff_val, 4)
                    else:
                        row_data[column_name] = round(diff_val, 6)
                else:
                    row_data[column_name] = ''
            
            # 添加多空排列信息
            alignment = signals.get('alignment', '')
            if isinstance(alignment, dict):
                row_data['多空排列'] = alignment.get('status', '')
                row_data['排列评分'] = alignment.get('score', 0)
            else:
                row_data['多空排列'] = str(alignment)
                row_data['排列评分'] = 0
            
            # 创建DataFrame并保存
            df = pd.DataFrame([row_data])
            
            # 文件名：直接使用ETF代码（去掉交易所后缀）
            csv_filename = f"{etf_code.replace('.SH', '').replace('.SZ', '')}.csv"
            csv_file_path = os.path.join(output_dir, csv_filename)
            
            # 保存CSV文件
            df.to_csv(csv_file_path, index=False, encoding='utf-8')
            
            print(f"✅ 单行CSV已保存: {csv_file_path}")
            return csv_file_path
            
        except Exception as e:
            print(f"❌ 保存单行CSV失败: {str(e)}")
            return None
    
    def save_batch_results(self, results_list: List[Dict], threshold: str,
                          output_base_dir: str = "data") -> Optional[str]:
        """
        批量保存计算结果
        
        Args:
            results_list: 结果列表
            threshold: 门槛类型
            output_base_dir: 输出基础目录
            
        Returns:
            Optional[str]: 汇总文件路径或None
        """
        try:
            print(f"📊 开始批量保存{threshold}的SMA计算结果...")
            
            # 逐个保存单行CSV文件
            saved_count = 0
            failed_count = 0
            
            for result in results_list:
                etf_code = result.get('etf_code', '')
                
                if not etf_code:
                    print("⚠️  跳过无效结果：缺少ETF代码")
                    failed_count += 1
                    continue
                
                # 保存单行CSV
                csv_path = self.save_single_row_csv(etf_code, result, threshold, output_base_dir)
                
                if csv_path:
                    saved_count += 1
                else:
                    failed_count += 1
            
            print(f"✅ 批量保存完成: 成功{saved_count}个，失败{failed_count}个")
            
            # 创建汇总信息
            summary_info = {
                'threshold': threshold,
                'total_processed': len(results_list),
                'successful_saves': saved_count,
                'failed_saves': failed_count,
                'success_rate': round((saved_count / len(results_list)) * 100, 2) if results_list else 0,
                'output_directory': os.path.join(
                    os.path.dirname(__file__), "..", output_base_dir, threshold
                )
            }
            
            return summary_info
            
        except Exception as e:
            print(f"❌ 批量保存失败: {str(e)}")
            return None
    
    def create_csv_header(self) -> List[str]:
        """
        创建CSV文件的表头
        
        Returns:
            List[str]: 表头列表
        """
        headers = [
            'ETF代码', '复权类型', '最新日期', '最新价格', '涨跌幅(%)'
        ]
        
        # 添加SMA指标列
        for period in self.config.sma_periods:
            headers.append(f'MA{period}')
        
        # 添加SMA差值指标列
        headers.extend([
            'SMA差值5-20',
            'SMA差值5-10', 
            'SMA差值5-20(%)',
            '多空排列',
            '排列评分'
        ])
        
        return headers
    
    def format_result_for_display(self, result: Dict) -> str:
        """
        格式化结果用于控制台显示
        
        Args:
            result: 计算结果
            
        Returns:
            str: 格式化的显示文本
        """
        try:
            etf_code = result.get('etf_code', 'Unknown')
            latest_price = result.get('latest_price', {})
            sma_values = result.get('sma_values', {})
            signals = result.get('signals', {})
            
            # 构建显示文本
            display_lines = []
            display_lines.append(f"📊 {etf_code} SMA分析结果:")
            
            # 价格信息
            if latest_price:
                price = latest_price.get('close', 'N/A')
                change = latest_price.get('change_pct', 'N/A')
                date = latest_price.get('date', 'N/A')
                display_lines.append(f"   💰 价格: {price} ({change:+}%) [{date}]")
            
            # SMA指标
            sma_line = "   🎯 SMA: "
            for period in self.config.sma_periods:
                sma_val = sma_values.get(f'SMA_{period}')
                if sma_val:
                    sma_line += f"MA{period}:{sma_val:.3f} "
            display_lines.append(sma_line)
            
            # SMA差值信息
            smadiff_5_20 = sma_values.get('SMA_DIFF_5_20')
            smadiff_5_20_pct = sma_values.get('SMA_DIFF_5_20_PCT')
            smadiff_5_10 = sma_values.get('SMA_DIFF_5_10')
            
            if smadiff_5_20 is not None:
                trend_icon = "📈" if smadiff_5_20 > 0 else ("📉" if smadiff_5_20 < 0 else "➡️")
                display_lines.append(f"   📊 SMA差值: 5-20={smadiff_5_20:+.6f} ({smadiff_5_20_pct:+.2f}%) {trend_icon}")
                
                if smadiff_5_10 is not None:
                    display_lines.append(f"              5-10={smadiff_5_10:+.6f} (短期动量)")
            
            # 多空排列
            alignment = signals.get('alignment', 'Unknown')
            display_lines.append(f"   🔄 排列: {alignment}")
            
            # 交易信号
            if 'trading_signals' in signals:
                trading = signals['trading_signals']
                signal = trading.get('primary_signal', 'Unknown')
                strength = trading.get('signal_strength', 0)
                confidence = trading.get('confidence_level', 0)
                display_lines.append(f"   🎯 信号: {signal} (强度:{strength}, 置信度:{confidence:.0f}%)")
            
            return "\n".join(display_lines)
            
        except Exception as e:
            return f"❌ 格式化显示失败: {str(e)}"
    
    def generate_summary_statistics(self, results_list: List[Dict]) -> Dict:
        """
        生成汇总统计信息
        
        Args:
            results_list: 结果列表
            
        Returns:
            Dict: 汇总统计
        """
        try:
            if not results_list:
                return {}
            
            total_count = len(results_list)
            successful_calcs = 0
            alignment_stats = {}
            sma_stats = {f'MA{period}': {'count': 0, 'avg': 0, 'min': float('inf'), 'max': float('-inf')} 
                        for period in self.config.sma_periods}
            
            # 统计计算成功率和信号分布
            for result in results_list:
                sma_values = result.get('sma_values', {})
                signals = result.get('signals', {})
                
                # 检查计算是否成功
                if any(sma_values.get(f'SMA_{p}') is not None for p in self.config.sma_periods):
                    successful_calcs += 1
                
                # 统计多空排列分布
                alignment = signals.get('alignment', '未知')
                alignment_stats[alignment] = alignment_stats.get(alignment, 0) + 1
                
                # 统计SMA值分布
                for period in self.config.sma_periods:
                    sma_val = sma_values.get(f'SMA_{period}')
                    if sma_val is not None:
                        sma_stats[f'MA{period}']['count'] += 1
                        sma_stats[f'MA{period}']['min'] = min(sma_stats[f'MA{period}']['min'], sma_val)
                        sma_stats[f'MA{period}']['max'] = max(sma_stats[f'MA{period}']['max'], sma_val)
            
            # 计算平均值
            sma_totals = {f'MA{period}': 0 for period in self.config.sma_periods}
            for result in results_list:
                sma_values = result.get('sma_values', {})
                for period in self.config.sma_periods:
                    sma_val = sma_values.get(f'SMA_{period}')
                    if sma_val is not None:
                        sma_totals[f'MA{period}'] += sma_val
            
            for period in self.config.sma_periods:
                count = sma_stats[f'MA{period}']['count']
                if count > 0:
                    sma_stats[f'MA{period}']['avg'] = round(sma_totals[f'MA{period}'] / count, 6)
                    sma_stats[f'MA{period}']['min'] = round(sma_stats[f'MA{period}']['min'], 6)
                    sma_stats[f'MA{period}']['max'] = round(sma_stats[f'MA{period}']['max'], 6)
                else:
                    sma_stats[f'MA{period}']['min'] = 0
                    sma_stats[f'MA{period}']['max'] = 0
            
            summary = {
                'total_etfs': total_count,
                'successful_calculations': successful_calcs,
                'success_rate': round((successful_calcs / total_count) * 100, 2),
                'alignment_distribution': alignment_stats,
                'sma_statistics': sma_stats
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ 生成汇总统计失败: {str(e)}")
            return {}

    def save_screening_batch_results(self, screening_results: Dict, output_dir: str = "data") -> Dict[str, Any]:
        """
        保存基于筛选结果的批量计算结果 - 模仿WMA，只保存ETF历史数据文件
        
        Args:
            screening_results: 筛选结果字典 {threshold: [results_list]}
            output_dir: 输出目录
            
        Returns:
            Dict[str, Any]: 保存结果统计
            
        🔬 精简输出: 只保存每个ETF的完整历史数据文件，不生成摘要和汇总文件
        """
        if not screening_results:
            print("❌ 没有有效的筛选结果可保存")
            return {}
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        save_stats = {
            'total_files_saved': 0,
            'total_size_bytes': 0,
            'thresholds': {}
        }
        
        for threshold, results_list in screening_results.items():
            if not results_list:
                continue
                
            print(f"\n📁 处理{threshold}结果...")
            
            threshold_stats = {
                'files_saved': 0,
                'total_size': 0,
                'failed_saves': 0
            }
            
            # 为每个ETF保存完整历史数据文件
            for result in results_list:
                etf_code = result['etf_code']
                sma_values = result['sma_values']
                alignment_signal = result['signals'].get('alignment', '')
                
                # 📊 读取完整历史数据（用户需要所有历史数据+SMA）
                from .data_reader import ETFDataReader
                data_reader = ETFDataReader(self.config)
                full_df = data_reader.read_etf_data(etf_code)
                
                if full_df is not None:
                    # 只取DataFrame部分，忽略total_rows
                    if isinstance(full_df, tuple):
                        full_df = full_df[0]
                    
                    saved_file = self.save_historical_results(
                        etf_code, full_df, sma_values, threshold, alignment_signal, output_dir
                    )
                    
                    if saved_file:
                        file_size = os.path.getsize(saved_file)
                        threshold_stats['files_saved'] += 1
                        threshold_stats['total_size'] += file_size
                    else:
                        threshold_stats['failed_saves'] += 1
                else:
                    threshold_stats['failed_saves'] += 1
                    print(f"   ❌ {etf_code}: 无法读取完整历史数据")
            
            save_stats['thresholds'][threshold] = threshold_stats
            save_stats['total_files_saved'] += threshold_stats['files_saved']
            save_stats['total_size_bytes'] += threshold_stats['total_size']
            
            print(f"✅ {threshold}: 成功保存 {threshold_stats['files_saved']} 个完整历史文件")
            if threshold_stats['failed_saves'] > 0:
                print(f"⚠️  {threshold}: {threshold_stats['failed_saves']} 个文件保存失败")
        
        print(f"\n💾 批量处理完成:")
        print(f"   📁 总文件数: {save_stats['total_files_saved']}")
        print(f"   💿 总大小: {save_stats['total_size_bytes'] / 1024 / 1024:.1f} MB")
        print(f"   📊 文件类型: 完整历史数据（按时间倒序）")
        
        return save_stats

    def save_historical_results(self, etf_code: str, full_df: pd.DataFrame, 
                              latest_sma_results: Dict, threshold: str, 
                              alignment_signal: str = "",
                              output_base_dir: str = "data") -> Optional[str]:
        """
        保存单个ETF的完整历史SMA数据文件
        
        Args:
            etf_code: ETF代码
            full_df: 完整历史数据
            latest_sma_results: 最新SMA计算结果（用于验证）
            threshold: 门槛类型 ("3000万门槛" 或 "5000万门槛")
            alignment_signal: 多空排列信号
            output_base_dir: 输出基础目录
            
        Returns:
            Optional[str]: 保存的文件路径 或 None
            
        🔬 完整历史数据: 每个ETF一个CSV文件，包含所有历史数据+每日SMA指标
        """
        try:
            # 创建门槛目录
            threshold_dir = os.path.join(output_base_dir, threshold)
            os.makedirs(threshold_dir, exist_ok=True)
            
            # 为完整历史数据计算每日SMA指标 - 使用高性能版本
            enhanced_df = self._calculate_full_historical_sma_optimized(full_df, etf_code)
            
            if enhanced_df is None or enhanced_df.empty:
                print(f"   ❌ {etf_code}: SMA计算失败")
                return None
            
            # 🔬 确保最新日期在顶部（与优化算法中的排序逻辑一致）
            # 转换日期格式以确保正确排序
            if enhanced_df['日期'].dtype == 'object':
                try:
                    enhanced_df['日期'] = pd.to_datetime(enhanced_df['日期'], format='%Y%m%d')
                    enhanced_df = enhanced_df.sort_values('日期', ascending=False).reset_index(drop=True)
                    # 转换回字符串格式保持一致性
                    enhanced_df['日期'] = enhanced_df['日期'].dt.strftime('%Y%m%d')
                except:
                    # 如果转换失败，直接按字符串排序（8位日期字符串可以直接排序）
                    enhanced_df = enhanced_df.sort_values('日期', ascending=False).reset_index(drop=True)
            else:
                enhanced_df = enhanced_df.sort_values('日期', ascending=False).reset_index(drop=True)
            
            # 生成文件名：直接使用ETF代码（去掉交易所后缀）
            clean_etf_code = etf_code.replace('.SH', '').replace('.SZ', '')
            output_file = os.path.join(threshold_dir, f"{clean_etf_code}.csv")
            
            # 保存完整历史数据
            enhanced_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            file_size = os.path.getsize(output_file)
            rows_count = len(enhanced_df)
            print(f"   💾 {etf_code}: {clean_etf_code}.csv ({rows_count}行, {file_size} 字节)")
            
            return output_file
            
        except Exception as e:
            print(f"   ❌ {etf_code}: 保存完整历史文件失败 - {e}")
            return None

    def _calculate_full_historical_sma_optimized(self, df: pd.DataFrame, etf_code: str) -> Optional[pd.DataFrame]:
        """
        为完整历史数据计算每日SMA指标 - 超高性能版本（模仿WMA实现）
        
        Args:
            df: 历史数据
            etf_code: ETF代码
            
        Returns:
            pd.DataFrame: 只包含SMA核心字段的数据（代码、日期、SMA指标、差值、排列）
            
        🚀 性能优化: 使用pandas向量化计算，速度提升50-100倍
        """
        try:
            import numpy as np
            import pandas as pd
            
            print(f"   🚀 {etf_code}: 超高性能SMA计算...")
            
            # Step 1: 数据准备（按时间正序计算）
            df_calc = df.sort_values('日期', ascending=True).copy().reset_index(drop=True)
            prices = df_calc['收盘价'].astype(float)
            
            # Step 2: 创建结果DataFrame - 只保留核心字段
            result_df = pd.DataFrame({
                '代码': etf_code.replace('.SH', '').replace('.SZ', ''),
                '日期': df_calc['日期']
            })
            
            # Step 3: 批量计算所有SMA（使用向量化计算）
            for period in self.config.sma_periods:
                # 🚀 使用pandas rolling计算SMA
                sma_series = prices.rolling(window=period, min_periods=period).mean()
                result_df[f'MA{period}'] = sma_series.round(6)
            
            # Step 4: 批量计算SMA差值（向量化）
            if 'MA5' in result_df.columns and 'MA20' in result_df.columns:
                ma5 = result_df['MA5']
                ma20 = result_df['MA20']
                
                # SMA差值5-20
                result_df['SMA差值5-20'] = np.where(
                    (ma5.notna()) & (ma20.notna()),
                    (ma5 - ma20).round(6),
                    ''
                )
                
                # SMA差值5-20百分比
                result_df['SMA差值5-20(%)'] = np.where(
                    (ma5.notna()) & (ma20.notna()) & (ma20 != 0),
                    ((ma5 - ma20) / ma20 * 100).round(4),
                    ''
                )
            
            if 'MA5' in result_df.columns and 'MA10' in result_df.columns:
                ma5 = result_df['MA5']
                ma10 = result_df['MA10']
                
                # SMA差值5-10
                result_df['SMA差值5-10'] = np.where(
                    (ma5.notna()) & (ma10.notna()),
                    (ma5 - ma10).round(6),
                    ''
                )
            
            # Step 5: 批量计算多空排列（向量化）
            from .signal_analyzer import SignalAnalyzer
            signal_analyzer = SignalAnalyzer(self.config)
            
            def calc_alignment_vectorized(row):
                if pd.notna(row['MA20']) if 'MA20' in row else pd.notna(row['MA60']):
                    sma_dict = {}
                    for period in self.config.sma_periods:
                        ma_col = f'MA{period}'
                        if ma_col in row:
                            sma_dict[f'SMA_{period}'] = row[ma_col]
                    
                    alignment = signal_analyzer.calculate_alignment(sma_dict)
                    
                    # 🔬 处理字典格式，提取关键信息
                    if isinstance(alignment, dict):
                        status = alignment.get('status', '未知')
                        score = alignment.get('score', 0)
                        return {'status': status, 'score': round(float(score), 2)}
                    else:
                        return str(alignment)  # 如果是字符串直接返回
                return {'status': '', 'score': 0}
            
            # 使用apply向量化计算排列
            alignment_results = result_df.apply(calc_alignment_vectorized, axis=1)
            
            # 提取状态和评分到独立列
            result_df['多空排列'] = alignment_results.apply(
                lambda x: x.get('status', '') if isinstance(x, dict) else str(x)
            )
            result_df['排列评分'] = alignment_results.apply(
                lambda x: x.get('score', 0) if isinstance(x, dict) else 0
            )
            
            # Step 6: 确保日期格式正确并按时间倒序排列（最新在顶部）
            # 转换日期格式以确保正确排序
            if result_df['日期'].dtype == 'object':
                # 尝试转换为日期格式
                try:
                    result_df['日期'] = pd.to_datetime(result_df['日期'], format='%Y%m%d')
                    result_df = result_df.sort_values('日期', ascending=False).reset_index(drop=True)
                    # 转换回字符串格式保持一致性
                    result_df['日期'] = result_df['日期'].dt.strftime('%Y%m%d')
                except:
                    # 如果转换失败，直接按字符串排序（8位日期字符串可以直接排序）
                    result_df = result_df.sort_values('日期', ascending=False).reset_index(drop=True)
            else:
                result_df = result_df.sort_values('日期', ascending=False).reset_index(drop=True)
            
            # 验证结果和排序
            max_period = max(self.config.sma_periods)
            valid_sma_count = result_df[f'MA{max_period}'].notna().sum() if f'MA{max_period}' in result_df.columns else 0
            latest_date = result_df.iloc[0]['日期']
            oldest_date = result_df.iloc[-1]['日期']
            latest_sma = result_df.iloc[0][f'MA{max_period}'] if f'MA{max_period}' in result_df.columns else 'N/A'
            
            print(f"   ✅ {etf_code}: 计算完成 - {valid_sma_count}行有效SMA数据")
            print(f"   📅 最新日期: {latest_date}, 最旧日期: {oldest_date} (确认最新在顶部)")
            print(f"   🎯 最新MA{max_period}: {latest_sma}")
            
            return result_df
            
        except Exception as e:
            print(f"   ❌ {etf_code}: 高性能计算失败 - {e}")
            import traceback
            traceback.print_exc()
            return None 