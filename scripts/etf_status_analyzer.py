#!/usr/bin/env python3
"""
ETF状态分析脚本
分析日更和周更数据差异，识别可能的下市和新上市ETF
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# 导入生命周期管理器和日志配置
from config.etf_lifecycle_manager import ETFLifecycleManager
from config.logger_config import setup_system_logger, get_report_paths

# 配置路径 - 使用项目根目录
DAILY_DIR = project_root / "ETF日更"
WEEKLY_DIR = project_root / "ETF周更"
CATEGORIES = ["0_ETF日K(前复权)", "0_ETF日K(后复权)", "0_ETF日K(除权)"]

def get_etf_codes_from_dir(directory: Path, category: str, include_delisted: bool = False) -> set:
    """获取指定目录和类别下的所有ETF代码"""
    category_path = directory / category
    if not category_path.exists():
        return set()
    
    codes = set()
    for filepath in category_path.glob('*.csv'):
        filename = filepath.name
        code = filename.replace('.csv', '')
        # 统一处理：移除交易所后缀（如.SZ, .SH）
        if '.' in code:
            code = code.split('.')[0]
        codes.add(code)
    
    # 如果不包含退市ETF，则过滤掉退市的
    if not include_delisted:
        # 获取生命周期管理器实例
        lifecycle_manager = ETFLifecycleManager()
        delisted_codes = {etf["code"] for etf in lifecycle_manager.get_delisted_etfs()}
        codes = codes - delisted_codes
    
    return codes

def analyze_etf_differences(daily_codes: set, weekly_codes: set, lifecycle_manager: ETFLifecycleManager) -> dict:
    """分析ETF差异"""
    # 获取已知的生命周期信息
    newly_listed_codes = {etf["code"] for etf in lifecycle_manager.get_newly_listed_etfs()}
    delisted_codes = {etf["code"] for etf in lifecycle_manager.get_delisted_etfs()}
    
    # 只在日更中的代码（可能是新上市）
    only_in_daily = daily_codes - weekly_codes
    # 只在周更中的代码（可能已下市）
    only_in_weekly = weekly_codes - daily_codes
    
    return {
        "total_daily": len(daily_codes),
        "total_weekly": len(weekly_codes),
        "common_codes": len(daily_codes & weekly_codes),
        "difference": len(daily_codes) - len(weekly_codes),
        "only_in_daily": {
            "codes": only_in_daily,
            "count": len(only_in_daily),
            "known_new_listed": only_in_daily & newly_listed_codes,
            "unknown_new": only_in_daily - newly_listed_codes
        },
        "only_in_weekly": {
            "codes": only_in_weekly,
            "count": len(only_in_weekly),
            "known_delisted": only_in_weekly & delisted_codes,
            "unknown_missing": only_in_weekly - delisted_codes
        },
        "lifecycle_status": {
            "total_delisted": len(delisted_codes),
            "total_newly_listed": len(newly_listed_codes),
            "delisted_codes": delisted_codes,
            "newly_listed_codes": newly_listed_codes
        }
    }

def analyze_etf_status(include_delisted: bool = False):
    """分析ETF状态"""
    logger = setup_system_logger()
    logger.info("🔍 开始分析ETF状态...")
    
    if include_delisted:
        logger.info("📋 包含退市ETF的完整分析")
    else:
        logger.info("📋 仅分析活跃ETF（默认模式）")
    
    # 初始化生命周期管理器
    lifecycle_manager = ETFLifecycleManager()
    
    # 获取各类别的ETF代码
    daily_codes = set()
    weekly_codes = set()
    
    logger.info("📊 收集ETF代码...")
    for category in CATEGORIES:
        daily_category_codes = get_etf_codes_from_dir(DAILY_DIR, category, include_delisted)
        weekly_category_codes = get_etf_codes_from_dir(WEEKLY_DIR, category, include_delisted)
        
        daily_codes.update(daily_category_codes)
        weekly_codes.update(weekly_category_codes)
        
        logger.info(f"  {category}:")
        logger.info(f"    日更: {len(daily_category_codes)} 个")
        logger.info(f"    周更: {len(weekly_category_codes)} 个")
    
    # 显示过滤信息
    if not include_delisted:
        delisted_count = len(lifecycle_manager.get_delisted_etfs())
        if delisted_count > 0:
            logger.info(f"🚫 已过滤 {delisted_count} 个退市ETF")
    
    logger.info(f"\n📋 总体统计:")
    logger.info(f"  日更总ETF数: {len(daily_codes)}")
    logger.info(f"  周更总ETF数: {len(weekly_codes)}")
    logger.info(f"  共同ETF数: {len(daily_codes & weekly_codes)}")
    logger.info(f"  数量差异: {len(daily_codes) - len(weekly_codes):+d}")
    
    # 分析差异
    analysis = analyze_etf_differences(daily_codes, weekly_codes, lifecycle_manager)
    
    logger.info(f"\n🔬 差异分析:")
    
    # 只在日更中的ETF（可能是新上市）
    if analysis["only_in_daily"]["count"] > 0:
        logger.info(f"📈 仅在日更中的ETF: {analysis['only_in_daily']['count']} 个")
        logger.info(f"    已知新上市: {len(analysis['only_in_daily']['known_new_listed'])} 个")
        logger.info(f"    未知新增: {len(analysis['only_in_daily']['unknown_new'])} 个")
        
        if analysis["only_in_daily"]["unknown_new"]:
            logger.info(f"    🤔 可能是新上市ETF:")
            for code in sorted(analysis["only_in_daily"]["unknown_new"]):
                logger.info(f"       - {code}")
    
    # 只在周更中的ETF（可能已下市）
    if analysis["only_in_weekly"]["count"] > 0:
        logger.info(f"📉 仅在周更中的ETF: {analysis['only_in_weekly']['count']} 个")
        logger.info(f"    已知下市: {len(analysis['only_in_weekly']['known_delisted'])} 个")
        logger.info(f"    未知缺失: {len(analysis['only_in_weekly']['unknown_missing'])} 个")
        
        if analysis["only_in_weekly"]["unknown_missing"]:
            logger.info(f"    🤔 可能已下市的ETF:")
            for code in sorted(analysis["only_in_weekly"]["unknown_missing"]):
                logger.info(f"       - {code}")
    
    # 显示当前生命周期状态
    logger.info(f"\n📊 生命周期管理状态:")
    newly_listed = lifecycle_manager.get_newly_listed_etfs()
    delisted = lifecycle_manager.get_delisted_etfs()
    
    logger.info(f"新上市ETF: {len(newly_listed)} 个")
    for etf in newly_listed:
        logger.info(f"  • {etf['code']} - {etf['name']} (上市: {etf['listing_date']})")
    
    logger.info(f"已退市ETF: {len(delisted)} 个")
    for etf in delisted:
        logger.info(f"  • {etf['code']} - {etf['name']} (退市: {etf['delisting_date']})")
    
    # 提供管理建议
    logger.info(f"\n💡 管理建议:")
    
    if analysis["only_in_daily"]["unknown_new"]:
        logger.info(f"   建议添加到新上市列表: {len(analysis['only_in_daily']['unknown_new'])} 个")
        logger.info(f"   命令: python scripts/etf_lifecycle_helper.py add-june-2025")
        
    if analysis["only_in_weekly"]["unknown_missing"]:
        logger.info(f"   建议添加到下市列表: {len(analysis['only_in_weekly']['unknown_missing'])} 个")
        logger.info(f"   命令: python scripts/etf_lifecycle_helper.py add-delisted <代码> <名称> <日期>")
    
    if not analysis["only_in_daily"]["unknown_new"] and not analysis["only_in_weekly"]["unknown_missing"]:
        logger.info(f"   ✅ 当前差异都已有记录，无需额外管理")
    
    return analysis

def generate_status_report(include_delisted: bool = False):
    """生成状态报告"""
    logger = setup_system_logger()
    logger.info("📄 生成ETF状态报告...")
    
    analysis = analyze_etf_status(include_delisted)
    lifecycle_manager = ETFLifecycleManager()
    lifecycle_report, _ = lifecycle_manager.generate_lifecycle_report()
    
    # 生成报告文件（转换set为list）
    def convert_sets_to_lists(obj):
        """递归转换set为list以便JSON序列化"""
        if isinstance(obj, set):
            return sorted(list(obj))
        elif isinstance(obj, dict):
            return {k: convert_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_sets_to_lists(item) for item in obj]
        else:
            return obj
    
    report = {
        "generated_time": datetime.now().isoformat(),
        "etf_analysis": convert_sets_to_lists(analysis),
        "lifecycle_report": lifecycle_report
    }
    
    # 保存报告到状态报告目录
    report_paths = get_report_paths()
    status_reports_dir = report_paths['status_reports']
    status_reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = status_reports_dir / f"etf_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📄 状态报告已保存: {report_file}")
    
    return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF状态分析器')
    parser.add_argument('--include-delisted', action='store_true', 
                       help='包含已退市ETF进行分析')
    
    args = parser.parse_args()
    
    logger = setup_system_logger()
    logger.info("🚀 ETF状态分析器启动")
    logger.info(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查目录是否存在
    if not DAILY_DIR.exists():
        logger.error(f"❌ 日更目录不存在: {DAILY_DIR}")
        return False
    
    if not WEEKLY_DIR.exists():
        logger.error(f"❌ 周更目录不存在: {WEEKLY_DIR}")
        return False
    
    try:
        # 分析ETF状态
        generate_status_report(args.include_delisted)
        
        logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("🎉 ETF状态分析完成！")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 分析过程中出现异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 