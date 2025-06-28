#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF初筛系统主入口
提供命令行接口和统一的运行入口
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import ETFDataLoader, ETFDataProcessor, OutputManager
from src.utils.config import get_config
from src.utils.logger import get_logger, ProcessTimer


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ETF初筛系统 - 基于11个字段筛选优质ETF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --mode all                    # 筛选所有ETF
  python main.py --mode specific --codes 159001 159003  # 筛选指定ETF
  python main.py --mode test                   # 测试系统
  python main.py --mode config                 # 显示配置信息
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["all", "specific", "test", "config", "dual"],
        default="dual",
        help="运行模式 (默认: dual 双门槛筛选)"
    )
    
    parser.add_argument(
        "--codes",
        nargs="+",
        help="指定ETF代码列表 (仅在specific模式下有效)"
    )
    
    parser.add_argument(
        "--fuquan-type",
        choices=["0_ETF日K(前复权)", "0_ETF日K(后复权)", "0_ETF日K(除权)"],
        default="0_ETF日K(后复权)",
        help="复权类型 (默认: 后复权)"
    )
    
    parser.add_argument(
        "--days-back",
        type=int,
        help="加载最近N天的数据 (默认: 全部)"
    )
    

    
    parser.add_argument(
        "--output-only",
        action="store_true",
        help="仅输出结果，不保存文件"
    )
    
    args = parser.parse_args()
    
    # 执行对应模式
    if args.mode == "test":
        run_system_test()
    elif args.mode == "config":
        show_config_info()
    elif args.mode == "all":
        run_all_etf_filter(args)
    elif args.mode == "specific":
        run_specific_etf_filter(args)
    elif args.mode == "dual":
        run_dual_threshold_filter(args)
    else:
        parser.print_help()


def run_system_test():
    """运行系统测试"""
    logger = get_logger()
    
    with ProcessTimer("系统测试", logger):
        try:
            # 1. 测试配置加载
            logger.info("🔧 测试配置加载...")
            config = get_config()
            if config.validate_config():
                logger.info("✅ 配置验证通过")
            else:
                logger.error("❌ 配置验证失败")
                return False
            
            # 2. 测试数据源
            logger.info("📊 测试数据源...")
            data_loader = ETFDataLoader()
            if data_loader.validate_data_source():
                logger.info("✅ 数据源验证通过")
            else:
                logger.error("❌ 数据源验证失败")
                return False
            
            # 3. 测试数据处理器
            logger.info("⚙️ 测试数据处理器...")
            processor = ETFDataProcessor()
            filter_descriptions = processor.get_filter_descriptions()
            logger.info(f"✅ 成功初始化 {len(filter_descriptions)} 个筛选器")
            
            # 4. 测试输出管理器
            logger.info("💾 测试输出管理器...")
            output_manager = OutputManager()
            output_summary = output_manager.get_output_summary()
            logger.info("✅ 输出管理器测试通过")
            
            logger.info("🎉 所有系统测试通过！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 系统测试失败: {e}")
            return False


def show_config_info():
    """显示配置信息"""
    logger = get_logger()
    
    try:
        config = get_config()
        
        # 显示配置摘要
        config.show_config_summary()
        
        # 显示筛选器信息
        processor = ETFDataProcessor()
        filter_descriptions = processor.get_filter_descriptions()
        
        logger.info("\n" + "="*50)
        logger.info("🔍 筛选器配置详情")
        logger.info("="*50)
        
        for name, desc in filter_descriptions.items():
            logger.info(f"\n📋 {name}:")
            if "筛选标准" in desc:
                for key, value in desc["筛选标准"].items():
                    logger.info(f"  • {key}: {value}")
        
        # 显示输出信息
        output_manager = OutputManager()
        output_summary = output_manager.get_output_summary()
        
        logger.info("\n" + "="*50)
        logger.info("💾 输出目录状态")
        logger.info("="*50)
        logger.info(f"输出路径: {output_summary['输出基础路径']}")
        
        for 复权类型, status in output_summary["复权目录状态"].items():
            status_icon = "✅" if status["存在"] else "❌"
            logger.info(f"{status_icon} {复权类型}: {status['ETF文件数']} 个文件")
        
    except Exception as e:
        logger.error(f"❌ 显示配置信息失败: {e}")


def run_dual_threshold_filter(args):
    """运行双门槛ETF筛选"""
    logger = get_logger()
    
    with ProcessTimer("双门槛ETF筛选", logger):
        try:
            from src.processors.data_processor import ETFDataProcessor
            
            # 显示双门槛筛选说明
            logger.info("🎯 双门槛筛选模式启动")
            logger.info("  • 5000万门槛：严格筛选优质ETF")
            logger.info("  • 3000万门槛：相对宽松的候选ETF")
            
            # 初始化处理器和输出管理器
            output_manager = OutputManager()
            
            # 5000万门槛筛选
            logger.info("\n🔸 执行5000万门槛筛选...")
            processor_5000w = ETFDataProcessor(threshold_name="5000万门槛")
            results_5000w = processor_5000w.process_all_etfs(
                复权类型=args.fuquan_type,
                days_back=args.days_back
            )
            
            if "error" in results_5000w:
                logger.error(f"❌ 5000万门槛筛选失败: {results_5000w['error']}")
                return False
            
            # 3000万门槛筛选
            logger.info("\n🔹 执行3000万门槛筛选...")
            processor_3000w = ETFDataProcessor(threshold_name="3000万门槛")
            results_3000w = processor_3000w.process_all_etfs(
                复权类型=args.fuquan_type,
                days_back=args.days_back
            )
            
            if "error" in results_3000w:
                logger.error(f"❌ 3000万门槛筛选失败: {results_3000w['error']}")
                return False
            
            # 显示对比结果摘要
            show_dual_threshold_summary(results_5000w, results_3000w, logger)
            
            # 保存双门槛结果
            if not args.output_only:
                logger.info(f"💾 保存双门槛筛选结果到 data 目录...")
                output_manager.save_dual_threshold_results(results_5000w, results_3000w)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 双门槛ETF筛选失败: {e}")
            return False


def run_all_etf_filter(args):
    """运行全量ETF筛选"""
    logger = get_logger()
    
    with ProcessTimer("全量ETF筛选", logger):
        try:
            # 初始化处理器
            processor = ETFDataProcessor()
            output_manager = OutputManager()
            
            # 执行筛选
            logger.info(f"🚀 开始筛选所有ETF ({args.fuquan_type})")
            results = processor.process_all_etfs(
                复权类型=args.fuquan_type,
                days_back=args.days_back
            )
            
            if "error" in results:
                logger.error(f"❌ 筛选失败: {results['error']}")
                return False
            
            # 显示结果摘要
            show_results_summary(results, logger)
            
            # 保存结果 - 简化输出：只保存代码列表
            if not args.output_only:
                logger.info(f"💾 保存筛选结果到 data 目录...")
                output_manager.save_simple_results(results, args.fuquan_type)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 全量ETF筛选失败: {e}")
            return False


def run_specific_etf_filter(args):
    """运行指定ETF筛选"""
    logger = get_logger()
    
    if not args.codes:
        logger.error("❌ 请使用 --codes 参数指定ETF代码")
        return False
    
    with ProcessTimer(f"指定ETF筛选({len(args.codes)}个)", logger):
        try:
            # 初始化处理器
            processor = ETFDataProcessor()
            output_manager = OutputManager()
            
            # 执行筛选
            logger.info(f"🎯 开始筛选指定ETF: {args.codes}")
            results = processor.process_specific_etfs(
                etf_codes=args.codes,
                复权类型=args.fuquan_type,
                days_back=args.days_back
            )
            
            if "error" in results:
                logger.error(f"❌ 筛选失败: {results['error']}")
                return False
            
            # 显示结果摘要
            show_results_summary(results, logger)
            
            # 保存结果 - 简化输出：只保存代码列表
            if not args.output_only:
                logger.info(f"💾 保存指定ETF筛选结果到 data 目录...")
                output_manager.save_simple_results(results, args.fuquan_type)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 指定ETF筛选失败: {e}")
            return False


def show_dual_threshold_summary(results_5000w: dict, results_3000w: dict, logger):
    """显示双门槛对比结果摘要"""
    try:
        logger.info("\n" + "="*80)
        logger.info("📊 双门槛ETF筛选对比结果")
        logger.info("="*80)
        
        # 5000万门槛结果
        筛选统计_5000w = results_5000w.get("最终结果", {}).get("筛选统计", {})
        通过ETF_5000w = results_5000w.get("通过ETF", [])
        候选ETF_5000w = results_5000w.get("最终结果", {}).get("候选ETF列表", [])
        
        # 3000万门槛结果
        筛选统计_3000w = results_3000w.get("最终结果", {}).get("筛选统计", {})
        通过ETF_3000w = results_3000w.get("通过ETF", [])
        候选ETF_3000w = results_3000w.get("最终结果", {}).get("候选ETF列表", [])
        
        logger.info(f"🔸 5000万门槛筛选结果:")
        logger.info(f"  • 完全通过: {筛选统计_5000w.get('完全通过', 0)} 个")
        logger.info(f"  • 候选ETF: {len(候选ETF_5000w)} 个")
        logger.info(f"  • 完全未通过: {筛选统计_5000w.get('完全未通过', 0)} 个")
        
        logger.info(f"\n🔹 3000万门槛筛选结果:")
        logger.info(f"  • 完全通过: {筛选统计_3000w.get('完全通过', 0)} 个")
        logger.info(f"  • 候选ETF: {len(候选ETF_3000w)} 个")
        logger.info(f"  • 完全未通过: {筛选统计_3000w.get('完全未通过', 0)} 个")
        
        # 对比分析
        增量通过 = len(通过ETF_3000w) - len(通过ETF_5000w)
        增量候选 = len(候选ETF_3000w) - len(候选ETF_5000w)
        
        logger.info(f"\n📈 增量分析 (3000万 vs 5000万):")
        logger.info(f"  • 通过ETF增量: +{增量通过} 个")
        logger.info(f"  • 候选ETF增量: +{增量候选} 个")
        
        # 显示部分通过的ETF
        if 通过ETF_5000w:
            logger.info(f"\n✅ 5000万门槛通过的优质ETF (前10个):")
            for i, etf_code in enumerate(通过ETF_5000w[:10], 1):
                logger.info(f"  {i:2d}. {etf_code}")
            if len(通过ETF_5000w) > 10:
                logger.info(f"     ... 还有 {len(通过ETF_5000w) - 10} 个")
        
        # 显示新增的通过ETF
        新增通过 = set(通过ETF_3000w) - set(通过ETF_5000w)
        if 新增通过:
            logger.info(f"\n🆕 3000万门槛新增通过的ETF (前5个):")
            for i, etf_code in enumerate(list(新增通过)[:5], 1):
                logger.info(f"  {i:2d}. {etf_code}")
            if len(新增通过) > 5:
                logger.info(f"     ... 还有 {len(新增通过) - 5} 个")
        
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"显示双门槛结果摘要失败: {e}")


def show_results_summary(results: dict, logger):
    """显示结果摘要"""
    try:
        logger.info("\n" + "="*60)
        logger.info("📊 ETF筛选结果摘要")
        logger.info("="*60)
        
        # 处理摘要
        处理摘要 = results.get("处理摘要", {})
        数据加载 = 处理摘要.get("数据加载", {})
        筛选统计 = results.get("最终结果", {}).get("筛选统计", {})
        
        logger.info(f"📈 数据处理:")
        logger.info(f"  • 发现ETF总数: {数据加载.get('发现ETF总数', 0)}")
        logger.info(f"  • 成功加载数: {数据加载.get('成功加载数', 0)}")
        logger.info(f"  • 加载成功率: {数据加载.get('加载成功率', 0):.1f}%")
        
        logger.info(f"\n🎯 筛选结果:")
        logger.info(f"  • 完全通过: {筛选统计.get('完全通过', 0)} 个")
        logger.info(f"  • 部分通过: {筛选统计.get('部分通过', 0)} 个")
        logger.info(f"  • 完全未通过: {筛选统计.get('完全未通过', 0)} 个")
        
        # 通过的ETF列表
        通过ETF = results.get("通过ETF", [])
        候选ETF = results.get("最终结果", {}).get("候选ETF列表", [])
        
        if 通过ETF:
            logger.info(f"\n✅ 通过筛选的ETF ({len(通过ETF)}个):")
            for i, etf_code in enumerate(通过ETF[:10], 1):  # 显示前10个
                logger.info(f"  {i:2d}. {etf_code}")
            if len(通过ETF) > 10:
                logger.info(f"     ... 还有 {len(通过ETF) - 10} 个")
        else:
            logger.info("\n❌ 没有ETF完全通过所有筛选器")
        
        if 候选ETF:
            logger.info(f"\n🎯 候选ETF ({len(候选ETF)}个):")
            for i, etf_code in enumerate(候选ETF[:5], 1):  # 显示前5个
                logger.info(f"  {i:2d}. {etf_code}")
            if len(候选ETF) > 5:
                logger.info(f"     ... 还有 {len(候选ETF) - 5} 个")
        
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"显示结果摘要失败: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        sys.exit(1) 