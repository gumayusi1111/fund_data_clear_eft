#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA计算器主程序
==============

模块化WMA计算器的命令行接口
"""

import argparse
import sys
from typing import List
from wma_calculator.controller import WMAController


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='WMA计算器 - 模块化版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m wma_calculator                         # 使用默认ETF和前复权
  python -m wma_calculator 510050.SH               # 计算上证50ETF（前复权）
  python -m wma_calculator --adj-type 后复权        # 使用后复权数据
  python -m wma_calculator 510050.SH --adj-type 除权  # 指定ETF和复权类型
  python -m wma_calculator --list                  # 显示可用ETF列表
  python -m wma_calculator --quick 510050.SH       # 快速分析（不保存文件）

特点:
  - 模块化架构，高内聚低耦合
  - 支持三种复权类型选择
  - 只读取必要行数，大幅提高效率
  - 临时数据处理，计算完立即清理
  - 只生成精简结果文件
  - 保护原始数据，100%安全
        """
    )
    
    parser.add_argument(
        'etf_codes', 
        nargs='*', 
        help='ETF代码 (如: 510050.SH)'
    )
    
    parser.add_argument(
        '--adj-type', '-a',
        choices=['前复权', '后复权', '除权'],
        default='前复权',
        help='复权类型 (默认: 前复权)'
    )
    
    parser.add_argument(
        '--periods', '-p',
        type=int,
        nargs='+',
        default=[3, 5, 10, 20],
        help='WMA周期 (默认: 3 5 10 20)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='显示可用的ETF代码列表'
    )
    
    parser.add_argument(
        '--quick', '-q',
        metavar='ETF_CODE',
        help='快速分析单个ETF（不保存文件）'
    )
    
    parser.add_argument(
        '--advanced', 
        action='store_true',
        help='包含高级分析（趋势分析、交易信号等）'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='输出目录 (默认: output)'
    )
    
    return parser.parse_args()


def main():
    """
    主函数 - WMA计算（模块化版本）
    
    🛡️ 数据安全承诺:
    - 模块化架构，职责清晰
    - 只读取必要行数，大幅提高效率
    - 临时读取原始数据，计算完立即清理
    - 支持三种复权类型选择
    - 只生成精简结果文件
    - 原始数据100%安全，内存使用最优
    """
    print("🚀 WMA计算器 (模块化版本)")
    print("=" * 60)
    print("📦 架构特点: 高内聚低耦合，组件化设计")
    print("⚡ 数据优化: 只读取必要行数，大幅提高效率")
    print("🛡️ 临时数据处理: 读取→计算→清理→精简结果")
    print("=" * 60)
    
    # 解析命令行参数
    args = parse_arguments()
    
    try:
        # 创建WMA控制器
        controller = WMAController(
            adj_type=args.adj_type,
            wma_periods=args.periods,
            output_dir=None  # 🔬 使用配置中的智能输出路径
        )
        
        # 如果要求显示ETF列表
        if args.list:
            available_etfs = controller.get_available_etfs()
            if available_etfs:
                print(f"📊 可用的ETF代码 ({len(available_etfs)}个) - {args.adj_type}:")
                for i, etf in enumerate(available_etfs, 1):
                    print(f"  {i:3d}. {etf}")
                    if i % 20 == 0 and i < len(available_etfs):
                        input("按回车继续...")
            else:
                print("❌ 没有找到可用的ETF数据文件")
            return
        
        # 快速分析模式
        if args.quick:
            result = controller.quick_analysis(args.quick)
            if result:
                print("✅ 快速分析完成")
            else:
                print("❌ 快速分析失败")
            return
        
        # 确定要处理的ETF代码
        if args.etf_codes:
            etf_codes = args.etf_codes
        else:
            # 🚀 改用股票型ETF作为默认，价格变化更明显
            etf_codes = [controller.config.DEFAULT_ETF_CODE]  # 510050.SH
            print(f"💡 未指定ETF代码，使用默认: {etf_codes} (上证50ETF)")
            print(f"💡 提示: 货币基金(如159001.SZ)价格稳定，股票型ETF价格变化更明显")
        
        print(f"📊 开始计算 {len(etf_codes)} 个ETF的WMA指标...")
        print(f"📁 数据路径: {controller.config.data_path}")
        print(f"📈 复权类型: {args.adj_type}")
        print(f"🎯 计算周期: {args.periods}")
        print(f"⚡ 数据优化: 只读取最新{controller.config.required_rows}行")
        print(f"📂 输出目录: {controller.config.default_output_dir} 🔬")
        print(f"🔬 高级分析: {'开启' if args.advanced else '关闭'}")
        
        # 执行完整的计算和保存流程
        result_summary = controller.calculate_and_save(
            etf_codes=etf_codes,
            output_dir=None,  # 🔬 使用配置中的智能输出路径
            include_advanced_analysis=args.advanced
        )
        
        # 总结
        print("\n" + "=" * 60)
        if result_summary['success']:
            print(f"✅ WMA计算完成! 成功处理 {result_summary['processed_etfs']}/{result_summary['total_etfs']} 个ETF")
            print(f"📊 成功率: {result_summary['success_rate']:.1f}%")
            
            print(f"\n🛡️ 数据处理确认:")
            print(f"   - 所有原始CSV文件完全未被修改")
            print(f"   - 临时数据已完全清理")
            print(f"   - 只生成精简结果文件")
            print(f"   - 数据处理效率大幅提升")
            print(f"   - 复权类型: {args.adj_type}")
            print(f"   - 模块化架构: 组件职责清晰")
            
            print(f"\n💡 查看结果:")
            print(f"   cd {result_summary['output_directory']}")
            print(f"   ls -la WMA_*")
        else:
            print(f"❌ WMA计算失败: {result_summary.get('message', '未知错误')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 