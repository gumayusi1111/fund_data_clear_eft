#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA计算器主程序 - 中短线专版
==========================

简单移动平均线计算器的命令行接口
专注于中短线交易指标：MA5, MA10, MA20, MA60

使用方法:
    python sma_main.py                                     # 默认：ETF筛选结果批量计算
    python sma_main.py --threshold 3000万门槛               # 仅计算3000万门槛
    python sma_main.py --threshold 5000万门槛               # 仅计算5000万门槛
    python sma_main.py --adj-type 后复权                   # 使用后复权数据
    
    python sma_main.py --etf 510050.SH                    # 单个ETF计算
    python sma_main.py --quick 510050.SH                  # 快速分析
    python sma_main.py --status                           # 系统状态
    
    🚀 模仿WMA：默认执行ETF筛选结果批量计算（3000万+5000万门槛）
"""

import argparse
import sys
import os
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(__file__))

from sma_calculator import SMAController


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SMA计算器 - 中短线专版 (MA5, MA10, MA20, MA60)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                                    # 默认：ETF筛选结果批量计算（3000万+5000万门槛）
  %(prog)s --threshold 3000万门槛               # 仅计算3000万门槛
  %(prog)s --threshold 5000万门槛               # 仅计算5000万门槛
  %(prog)s --adj-type 后复权                   # 使用后复权数据
  
  %(prog)s --etf 510050.SH                    # 计算单个ETF的SMA
  %(prog)s --quick 510050.SH                  # 快速分析单个ETF
  %(prog)s --status                           # 查看系统状态
  %(prog)s --list                             # 列出可用的ETF代码

中短线指标说明:
  MA5  : 5日移动平均线 (超短期趋势)
  MA10 : 10日移动平均线 (短期趋势)
  MA20 : 20日移动平均线 (月线趋势)
  MA60 : 60日移动平均线 (季线趋势)
  
🚀 模仿WMA：默认执行ETF筛选结果批量计算
        """
    )
    
    # 互斥的操作组（不再是required，允许默认操作）
    operation_group = parser.add_mutually_exclusive_group(required=False)
    operation_group.add_argument('--etf', type=str, help='计算单个ETF的SMA指标')
    operation_group.add_argument('--quick', type=str, help='快速分析单个ETF（不保存文件）')
    operation_group.add_argument('--status', action='store_true', help='显示系统状态')
    operation_group.add_argument('--list', action='store_true', help='列出可用的ETF代码')
    
    # 可选参数
    parser.add_argument('--adj-type', type=str, default='前复权',
                       choices=['前复权', '后复权', '除权'],
                       help='复权类型 (默认: 前复权)')
    
    parser.add_argument('--threshold', type=str,
                       choices=['3000万门槛', '5000万门槛'],
                       help='指定门槛类型（默认：处理所有门槛）')
    
    parser.add_argument('--periods', type=int, nargs='+', 
                       default=[5, 10, 20, 60],
                       help='SMA周期列表 (默认: 5 10 20 60)')
    
    parser.add_argument('--output-dir', type=str, 
                       help='输出目录路径')
    
    parser.add_argument('--advanced', action='store_true',
                       help='包含高级分析（趋势分析、交易信号等）')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细信息')
    
    args = parser.parse_args()
    
    # 显示程序信息
    print("=" * 80)
    print("🚀 SMA计算器启动 - 中短线专版")
    print("📊 支持指标: MA5, MA10, MA20, MA60")
    print("⏰ 启动时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 80)
    
    try:
        # 初始化控制器
        if args.verbose:
            print("🔧 初始化SMA控制器...")
        
        controller = SMAController(
            adj_type=getattr(args, 'adj_type', '前复权'),
            sma_periods=args.periods,
            output_dir=getattr(args, 'output_dir', None)  # 处理参数名变化
        )
        
        # 🚀 默认执行ETF筛选结果批量计算（模仿WMA）
        if not any([args.etf, args.quick, args.status, args.list]):
            # 默认模式：筛选批量计算
            print("🔍 默认模式：ETF筛选结果批量计算...")
            
            # 确定要处理的门槛
            if args.threshold:
                thresholds = [args.threshold]
                print(f"📊 指定门槛: {args.threshold}")
            else:
                thresholds = ["3000万门槛", "5000万门槛"]
                print(f"📊 处理所有门槛: {', '.join(thresholds)}")
            
            # 执行筛选结果批量计算
            result_summary = controller.calculate_and_save_screening_results(
                thresholds=thresholds,
                output_dir=getattr(args, 'output_dir', None),
                include_advanced_analysis=args.advanced
            )
            
            # 输出筛选批量处理结果
            print("\n" + "=" * 60)
            if result_summary['success']:
                print(f"✅ ETF筛选批量计算完成! 成功处理 {result_summary['total_etfs_processed']} 个ETF")
                print(f"📊 门槛数量: {result_summary['thresholds_processed']}")
                print(f"📁 输出目录: {result_summary['output_directory']}")
                
                # 显示保存统计
                save_stats = result_summary['save_statistics']
                print(f"💾 历史文件: {save_stats['total_files_saved']} 个")
                print(f"💿 总大小: {save_stats['total_size_bytes'] / 1024 / 1024:.1f} MB")
                
                print(f"\n🛡️ 数据处理确认:")
                print(f"   - 基于ETF初筛结果进行批量计算")
                print(f"   - 每个ETF生成独立的历史数据文件")
                print(f"   - 包含完整历史数据 + 最新SMA指标")
                print(f"   - 按门槛分类保存到对应目录")
                print(f"   - 复权类型: {args.adj_type}")
                print(f"   - 模块化架构: 组件职责清晰")
                
                return 0
            else:
                print(f"❌ ETF筛选批量计算失败: {result_summary.get('message', '未知错误')}")
                return 1
        
        # 执行相应操作
        if args.etf:
            # 单个ETF计算
            result = handle_single_etf(controller, args.etf, args.verbose)
            return 0 if result else 1
            
        elif args.quick:
            # 快速分析
            result = handle_quick_analysis(controller, args.quick)
            return 0 if result else 1
            
        elif args.status:
            # 系统状态
            handle_system_status(controller)
            return 0
            
        elif args.list:
            # 列出ETF代码
            handle_list_etfs(controller)
            return 0
    
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        return 1
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def handle_single_etf(controller: SMAController, etf_code: str, verbose: bool = False) -> bool:
    """处理单个ETF"""
    print(f"\n🎯 计算单个ETF: {etf_code}")
    print("-" * 50)
    
    # 验证ETF代码
    if not controller.validate_etf_code(etf_code):
        print(f"❌ ETF代码无效: {etf_code}")
        return False
    
    # 执行计算
    result = controller.process_single_etf(etf_code, include_advanced_analysis=verbose)
    
    if result:
        print(f"\n✅ {etf_code} 计算完成")
        
        # 显示结果摘要
        latest = result['latest_price']
        sma_values = result['sma_values']
        signals = result['signals']
        
        print(f"\n📊 结果摘要:")
        print(f"   💰 最新价格: {latest['close']} ({latest['change_pct']:+.2f}%)")
        print(f"   📅 数据日期: {latest['date']}")
        
        print(f"   🎯 SMA指标:")
        for period in controller.config.sma_periods:
            sma_val = sma_values.get(f'SMA_{period}')
            if sma_val:
                print(f"      MA{period}: {sma_val:.6f}")
        
        # SMA差值信息
        smadiff_5_20 = sma_values.get('SMA_DIFF_5_20')
        smadiff_5_20_pct = sma_values.get('SMA_DIFF_5_20_PCT')
        smadiff_5_10 = sma_values.get('SMA_DIFF_5_10')
        
        if smadiff_5_20 is not None:
            print(f"   📊 SMA差值:")
            trend_icon = "📈" if smadiff_5_20 > 0 else ("📉" if smadiff_5_20 < 0 else "➡️")
            print(f"      MA5-MA20: {smadiff_5_20:+.6f} ({smadiff_5_20_pct:+.2f}%) {trend_icon}")
            
            if smadiff_5_10 is not None:
                print(f"      MA5-MA10: {smadiff_5_10:+.6f}")
        
        print(f"   🔄 多空排列: {signals['alignment']}")
        
        if verbose and 'trading_signals' in signals:
            trading = signals['trading_signals']
            print(f"   🎯 交易信号: {trading['primary_signal']}")
            print(f"   💪 信号强度: {trading['signal_strength']}")
            print(f"   🎲 置信度: {trading['confidence_level']:.0f}%")
        
        return True
    else:
        print(f"❌ {etf_code} 计算失败")
        return False


def handle_quick_analysis(controller: SMAController, etf_code: str) -> bool:
    """处理快速分析"""
    print(f"\n⚡ 快速分析: {etf_code}")
    print("-" * 50)
    
    result = controller.quick_analysis(etf_code)
    return result is not None





def handle_system_status(controller: SMAController):
    """处理系统状态"""
    print(f"\n🔧 系统状态检查")
    print("-" * 50)
    
    status = controller.get_system_status()
    
    if 'error' in status:
        print(f"❌ {status['error']}")
        return
    
    # 系统信息
    sys_info = status['system_info']
    print(f"📋 系统信息:")
    print(f"   版本: {sys_info['version']}")
    print(f"   配置: {sys_info['config']}")
    print(f"   数据路径: {sys_info['data_path']}")
    print(f"   输出路径: {sys_info['output_path']}")
    
    # 数据状态
    data_status = status['data_status']
    print(f"\n📊 数据状态:")
    print(f"   可用ETF数量: {data_status['available_etfs_count']}")
    print(f"   数据路径有效: {'✅' if data_status['data_path_valid'] else '❌'}")
    
    if data_status['sample_etfs']:
        print(f"   示例ETF: {', '.join(data_status['sample_etfs'])}")
    
    # 组件状态
    components = status['components']
    print(f"\n🧩 组件状态:")
    for comp_name, comp_status in components.items():
        status_icon = "✅" if comp_status == "Ready" else "❌"
        print(f"   {comp_name}: {status_icon} {comp_status}")


def handle_list_etfs(controller: SMAController):
    """列出可用的ETF代码"""
    print(f"\n📋 可用ETF代码列表")
    print("-" * 50)
    
    etf_codes = controller.get_available_etfs()
    
    if etf_codes:
        print(f"📊 共找到 {len(etf_codes)} 个ETF:")
        
        # 分组显示
        for i in range(0, len(etf_codes), 10):
            batch = etf_codes[i:i+10]
            print(f"   {', '.join(batch)}")
        
        print(f"\n💡 使用示例:")
        print(f"   python sma_main.py --etf {etf_codes[0]}")
        print(f"   python sma_main.py --quick {etf_codes[0]}")
    else:
        print("❌ 未找到可用的ETF数据")


if __name__ == "__main__":
    sys.exit(main()) 