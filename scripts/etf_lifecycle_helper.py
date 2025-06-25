#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF生命周期管理助手
命令行工具，用于方便地管理新上市和退市ETF
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from config.etf_lifecycle_manager import ETFLifecycleManager

def add_delisted_etf(args):
    """添加退市ETF"""
    manager = ETFLifecycleManager()
    
    success = manager.add_delisted_etf(
        code=args.code,
        name=args.name,
        delisting_date=args.date,
        reason=args.reason or "未知原因"
    )
    
    if success:
        print(f"✅ 成功添加退市ETF: {args.code} - {args.name}")
        print(f"   退市日期: {args.date}")
        print(f"   退市原因: {args.reason or '未知原因'}")
    else:
        print(f"❌ 添加退市ETF失败: {args.code}")
    
    return success

def remove_delisted_etf(args):
    """移除退市ETF"""
    manager = ETFLifecycleManager()
    
    success = manager.remove_delisted_etf(args.code)
    
    if success:
        print(f"✅ 成功移除退市ETF: {args.code}")
    else:
        print(f"❌ 移除退市ETF失败: {args.code}")
    
    return success

def list_delisted_etfs(args):
    """列出所有退市ETF"""
    manager = ETFLifecycleManager()
    
    delisted_etfs = manager.get_delisted_etfs()
    
    if not delisted_etfs:
        print("📋 当前没有记录的退市ETF")
        return True
    
    print(f"📋 退市ETF列表 (共{len(delisted_etfs)}个):")
    print("-" * 80)
    
    for i, etf in enumerate(delisted_etfs, 1):
        print(f"{i:2d}. {etf['code']:8s} - {etf['name']:30s}")
        print(f"    退市日期: {etf['delisting_date']:10s}  退市原因: {etf['reason']}")
        if 'added_date' in etf:
            print(f"    记录时间: {etf['added_date']}")
        print()
    
    return True

def list_newly_listed_etfs(args):
    """列出所有新上市ETF"""
    manager = ETFLifecycleManager()
    
    newly_listed_etfs = manager.get_newly_listed_etfs()
    
    if not newly_listed_etfs:
        print("📋 当前没有记录的新上市ETF")
        return True
    
    print(f"📋 新上市ETF列表 (共{len(newly_listed_etfs)}个):")
    print("-" * 80)
    
    for i, etf in enumerate(newly_listed_etfs, 1):
        print(f"{i:2d}. {etf['code']:8s} - {etf['name']:30s}")
        print(f"    上市日期: {etf['listing_date']:10s}")
        if 'added_date' in etf:
            print(f"    记录时间: {etf['added_date']}")
        print()
    
    return True

def check_etf_status(args):
    """检查ETF状态"""
    manager = ETFLifecycleManager()
    
    lifecycle_info = manager.get_etf_lifecycle_info(args.code)
    
    print(f"🔍 ETF {args.code} 生命周期信息:")
    print("-" * 40)
    
    status = lifecycle_info['status']
    info = lifecycle_info['info']
    
    if status == "newly_listed":
        print("📈 状态: 新上市ETF")
        print(f"   名称: {info['name']}")
        print(f"   上市日期: {info['listing_date']}")
    elif status == "delisted":
        print("📉 状态: 已退市ETF")
        print(f"   名称: {info['name']}")
        print(f"   退市日期: {info['delisting_date']}")
        print(f"   退市原因: {info['reason']}")
    else:
        print("📊 状态: 正常交易ETF")
        print("   无特殊生命周期记录")
    
    # 检查当前是否活跃
    is_active = manager.is_etf_active(args.code)
    print(f"   当前状态: {'🟢 活跃' if is_active else '🔴 非活跃'}")
    
    return True

def add_june_2025_listings(args):
    """批量添加2025年6月新上市ETF"""
    manager = ETFLifecycleManager()
    
    print("📦 批量添加2025年6月新上市ETF...")
    success = manager.add_june_2025_new_listings()
    
    if success:
        print("✅ 成功添加所有2025年6月新上市ETF")
    else:
        print("⚠️ 部分ETF添加失败，请检查日志")
    
    return success

def generate_summary_report(args):
    """生成汇总报告"""
    manager = ETFLifecycleManager()
    
    newly_listed = manager.get_newly_listed_etfs()
    delisted = manager.get_delisted_etfs()
    
    print("📊 ETF生命周期汇总报告")
    print("=" * 50)
    
    print(f"📈 新上市ETF: {len(newly_listed)} 个")
    if newly_listed:
        recent_listings = [etf for etf in newly_listed if etf['listing_date'] >= '2025-01-01']
        print(f"   其中2025年新上市: {len(recent_listings)} 个")
    
    print(f"📉 已退市ETF: {len(delisted)} 个")
    if delisted:
        recent_delistings = [etf for etf in delisted if etf['delisting_date'] >= '2025-01-01']
        print(f"   其中2025年退市: {len(recent_delistings)} 个")
    
    print(f"📋 总生命周期事件: {len(newly_listed) + len(delisted)} 个")
    
    # 生成详细报告文件
    report, report_path = manager.generate_lifecycle_report()
    if report_path:
        print(f"\n📄 详细报告已保存至: {report_path}")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ETF生命周期管理助手',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 添加退市ETF
  python etf_lifecycle_helper.py add-delisted 159999 "某退市ETF" 2025-03-15 --reason "规模过小清盘"
  
  # 查看所有退市ETF
  python etf_lifecycle_helper.py list-delisted
  
  # 查看ETF状态
  python etf_lifecycle_helper.py check-status 159228
  
  # 批量添加6月新上市ETF
  python etf_lifecycle_helper.py add-june-2025
  
  # 生成汇总报告
  python etf_lifecycle_helper.py summary
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加退市ETF
    parser_add_delisted = subparsers.add_parser('add-delisted', help='添加退市ETF')
    parser_add_delisted.add_argument('code', help='ETF代码')
    parser_add_delisted.add_argument('name', help='ETF名称')
    parser_add_delisted.add_argument('date', help='退市日期 (YYYY-MM-DD)')
    parser_add_delisted.add_argument('--reason', help='退市原因')
    parser_add_delisted.set_defaults(func=add_delisted_etf)
    
    # 移除退市ETF
    parser_remove_delisted = subparsers.add_parser('remove-delisted', help='移除退市ETF记录')
    parser_remove_delisted.add_argument('code', help='ETF代码')
    parser_remove_delisted.set_defaults(func=remove_delisted_etf)
    
    # 列出退市ETF
    parser_list_delisted = subparsers.add_parser('list-delisted', help='列出所有退市ETF')
    parser_list_delisted.set_defaults(func=list_delisted_etfs)
    
    # 列出新上市ETF
    parser_list_new = subparsers.add_parser('list-newly-listed', help='列出所有新上市ETF')
    parser_list_new.set_defaults(func=list_newly_listed_etfs)
    
    # 检查ETF状态
    parser_check = subparsers.add_parser('check-status', help='检查ETF生命周期状态')
    parser_check.add_argument('code', help='ETF代码')
    parser_check.set_defaults(func=check_etf_status)
    
    # 批量添加6月新上市ETF
    parser_june = subparsers.add_parser('add-june-2025', help='批量添加2025年6月新上市ETF')
    parser_june.set_defaults(func=add_june_2025_listings)
    
    # 生成汇总报告
    parser_summary = subparsers.add_parser('summary', help='生成生命周期汇总报告')
    parser_summary.set_defaults(func=generate_summary_report)
    
    # 解析参数
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return False
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断操作")
        return False
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 