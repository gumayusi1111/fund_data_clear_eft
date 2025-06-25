#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF生命周期管理辅助脚本
提供命令行接口来管理ETF的上市、下市等生命周期事件
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from config.etf_lifecycle_manager import ETFLifecycleManager, quick_add_june_2025_etfs
from config.logger_config import setup_lifecycle_logger

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ETF生命周期管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加新上市ETF
    add_new_parser = subparsers.add_parser('add-new', help='添加新上市ETF')
    add_new_parser.add_argument('code', help='ETF代码')
    add_new_parser.add_argument('name', help='ETF名称')
    add_new_parser.add_argument('date', help='上市日期(YYYY-MM-DD)')
    add_new_parser.add_argument('--note', default='', help='备注信息')
    
    # 添加下市ETF
    add_delisted_parser = subparsers.add_parser('add-delisted', help='添加下市ETF')
    add_delisted_parser.add_argument('code', help='ETF代码')
    add_delisted_parser.add_argument('name', help='ETF名称')
    add_delisted_parser.add_argument('date', help='下市日期(YYYY-MM-DD)')
    add_delisted_parser.add_argument('--reason', default='', help='下市原因')
    
    # 查看状态
    subparsers.add_parser('status', help='查看ETF生命周期状态')
    
    # 生成报告
    subparsers.add_parser('report', help='生成生命周期报告')
    
    # 快速添加2025年6月新上市ETF
    subparsers.add_parser('add-june-2025', help='快速添加2025年6月新上市的ETF')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 初始化管理器
    manager = ETFLifecycleManager()
    logger = setup_lifecycle_logger()
    
    try:
        if args.command == 'add-new':
            success = manager.add_newly_listed_etf(args.code, args.name, args.date, args.note)
            if success:
                logger.info(f"✅ 成功添加新上市ETF: {args.code} - {args.name}")
            else:
                logger.warning(f"⚠️  ETF {args.code} 已存在或添加失败")
                
        elif args.command == 'add-delisted':
            success = manager.add_delisted_etf(args.code, args.name, args.date, args.reason)
            if success:
                logger.info(f"✅ 成功添加下市ETF: {args.code} - {args.name}")
            else:
                logger.warning(f"⚠️  ETF {args.code} 已存在或添加失败")
                
        elif args.command == 'status':
            newly_listed = manager.get_newly_listed_etfs()
            delisted = manager.get_delisted_etfs()
            
            logger.info("📊 ETF生命周期状态")
            logger.info(f"新上市ETF: {len(newly_listed)} 个")
            for etf in newly_listed:
                logger.info(f"  • {etf['code']} - {etf['name']} (上市: {etf['listing_date']})")
            
            logger.info(f"已下市ETF: {len(delisted)} 个")
            for etf in delisted:
                logger.info(f"  • {etf['code']} - {etf['name']} (下市: {etf['delisting_date']})")
                
        elif args.command == 'report':
            report, report_path = manager.generate_lifecycle_report()
            logger.info(f"📄 生命周期报告已生成: {report_path}")
            logger.info(f"新上市ETF: {report['newly_listed_count']} 个")
            logger.info(f"已下市ETF: {report['delisted_count']} 个")
            
        elif args.command == 'add-june-2025':
            count = quick_add_june_2025_etfs()
            logger.info(f"✅ 已添加 {count} 个2025年6月新上市的ETF")
            
    except Exception as e:
        logger.error(f"❌ 执行命令时发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 