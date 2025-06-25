#!/usr/bin/env python3
"""
ETF数据验证脚本
1. 验证日更和周更数据的一致性
2. 随机抽取100个ETF代码验证三种复权数据的可信度
3. 生成详细的验证报告
"""

import os
import sys
import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json

# 添加config目录到路径
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
sys.path.insert(0, config_dir)

try:
    import importlib.util
    # 导入日志配置
    logger_config_path = os.path.join(config_dir, 'logger_config.py')
    spec = importlib.util.spec_from_file_location("logger_config", logger_config_path)
    logger_config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(logger_config_module)
    setup_logger = logger_config_module.setup_logger
    
    # 设置验证专用日志
    logger = setup_logger("etf_validation", "general")
except ImportError as e:
    print(f"警告：无法导入日志配置: {e}")
    logger = None

# 配置路径
DAILY_DIR = "./ETF日更"
WEEKLY_DIR = "./ETF周更"
CATEGORIES = ["0_ETF日K(前复权)", "0_ETF日K(后复权)", "0_ETF日K(除权)"]

def log_message(message: str, level: str = "INFO"):
    """记录日志消息"""
    if logger:
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    # 同时输出到控制台
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_etf_codes_from_dir(directory: str, category: str) -> List[str]:
    """获取指定目录和类别下的所有ETF代码"""
    category_path = os.path.join(directory, category)
    if not os.path.exists(category_path):
        return []
    
    codes = []
    for filename in os.listdir(category_path):
        if filename.endswith('.csv'):
            code = filename.replace('.csv', '')
            codes.append(code)
    
    return sorted(codes)


def load_etf_data(directory: str, category: str, code: str) -> Optional[pd.DataFrame]:
    """加载指定ETF的数据"""
    file_path = os.path.join(directory, category, f"{code}.csv")
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if df.empty:
            return None
        
        # 确保日期列为字符串类型便于比较
        df['日期'] = df['日期'].astype(str)
        return df
    except Exception as e:
        log_message(f"加载数据失败 {file_path}: {e}", "ERROR")
        return None


def compare_daily_weekly_consistency():
    """比较日更和周更数据的一致性"""
    log_message("🔍 开始验证日更和周更数据一致性...")
    
    results = {
        "total_codes": 0,
        "consistent_codes": 0,
        "inconsistent_codes": 0,
        "missing_in_daily": 0,
        "missing_in_weekly": 0,
        "inconsistent_details": []
    }
    
    # 对每个类别进行检查
    for category in CATEGORIES:
        log_message(f"📊 检查类别: {category}")
        
        # 获取两边的ETF代码
        daily_codes = set(get_etf_codes_from_dir(DAILY_DIR, category))
        weekly_codes = set(get_etf_codes_from_dir(WEEKLY_DIR, category))
        
        log_message(f"  日更ETF数量: {len(daily_codes)}")
        log_message(f"  周更ETF数量: {len(weekly_codes)}")
        
        # 找出共同的ETF代码
        common_codes = daily_codes & weekly_codes
        missing_in_daily = weekly_codes - daily_codes
        missing_in_weekly = daily_codes - weekly_codes
        
        log_message(f"  共同ETF数量: {len(common_codes)}")
        if missing_in_daily:
            log_message(f"  ⚠️ 日更缺失: {len(missing_in_daily)} 个")
        if missing_in_weekly:
            log_message(f"  ⚠️ 周更缺失: {len(missing_in_weekly)} 个")
        
        results["missing_in_daily"] += len(missing_in_daily)
        results["missing_in_weekly"] += len(missing_in_weekly)
        
        # 随机抽取一些代码进行详细比较
        sample_codes = random.sample(list(common_codes), min(10, len(common_codes)))
        
        for code in sample_codes:
            daily_df = load_etf_data(DAILY_DIR, category, code)
            weekly_df = load_etf_data(WEEKLY_DIR, category, code)
            
            if daily_df is None or weekly_df is None:
                continue
            
            results["total_codes"] += 1
            
            # 比较共同日期的数据
            daily_dates = set(daily_df['日期'])
            weekly_dates = set(weekly_df['日期'])
            common_dates = daily_dates & weekly_dates
            
            if not common_dates:
                log_message(f"  ⚠️ {code}: 没有共同日期数据", "WARNING")
                continue
            
            # 取最近的几个日期进行比较
            recent_dates = sorted(list(common_dates))[-5:]  # 最近5天
            
            is_consistent = True
            for date in recent_dates:
                daily_row = daily_df[daily_df['日期'] == date]
                weekly_row = weekly_df[weekly_df['日期'] == date]
                
                if daily_row.empty or weekly_row.empty:
                    continue
                
                # 比较价格字段（允许小的浮点误差）
                price_fields = ['开盘价', '最高价', '最低价', '收盘价']
                for field in price_fields:
                    if field in daily_row.columns and field in weekly_row.columns:
                        daily_val = float(daily_row[field].iloc[0])
                        weekly_val = float(weekly_row[field].iloc[0])
                        
                        # 允许0.01的误差（1分钱）
                        if abs(daily_val - weekly_val) > 0.01:
                            is_consistent = False
                            results["inconsistent_details"].append({
                                "code": code,
                                "category": category,
                                "date": date,
                                "field": field,
                                "daily_value": daily_val,
                                "weekly_value": weekly_val,
                                "difference": abs(daily_val - weekly_val)
                            })
            
            if is_consistent:
                results["consistent_codes"] += 1
            else:
                results["inconsistent_codes"] += 1
    
    return results


def validate_three_adjustments_accuracy():
    """验证三种复权数据的准确性"""
    log_message("🔬 开始验证三种复权数据准确性...")
    
    # 随机选择100个ETF代码进行验证
    all_codes = get_etf_codes_from_dir(DAILY_DIR, CATEGORIES[0])  # 从前复权目录获取代码
    sample_codes = random.sample(all_codes, min(100, len(all_codes)))
    
    log_message(f"📝 随机抽取 {len(sample_codes)} 个ETF进行验证")
    
    results = {
        "total_samples": len(sample_codes),
        "valid_samples": 0,
        "calculation_errors": 0,
        "price_anomalies": 0,
        "adjustment_accuracy": {
            "high_accuracy": 0,    # 差异 < 0.1%
            "medium_accuracy": 0,  # 差异 0.1% - 1%
            "low_accuracy": 0,     # 差异 > 1%
        },
        "details": []
    }
    
    for i, code in enumerate(sample_codes, 1):
        if i % 20 == 0:
            log_message(f"  进度: {i}/{len(sample_codes)}")
        
        # 加载三种复权数据
        forward_df = load_etf_data(DAILY_DIR, "0_ETF日K(前复权)", code)
        backward_df = load_etf_data(DAILY_DIR, "0_ETF日K(后复权)", code)
        no_adjust_df = load_etf_data(DAILY_DIR, "0_ETF日K(除权)", code)
        
        if any(df is None for df in [forward_df, backward_df, no_adjust_df]):
            continue
        
        # 找到共同日期
        forward_dates = set(forward_df['日期'])
        backward_dates = set(backward_df['日期'])
        no_adjust_dates = set(no_adjust_df['日期'])
        common_dates = forward_dates & backward_dates & no_adjust_dates
        
        if not common_dates:
            continue
        
        results["valid_samples"] += 1
        
        # 随机选择几个日期进行验证
        test_dates = random.sample(list(common_dates), min(5, len(common_dates)))
        
        code_errors = []
        for date in test_dates:
            forward_row = forward_df[forward_df['日期'] == date].iloc[0]
            backward_row = backward_df[backward_df['日期'] == date].iloc[0]
            no_adjust_row = no_adjust_df[no_adjust_df['日期'] == date].iloc[0]
            
            # 验证复权计算的一致性
            # 理论上：前复权价 × 后复权价 / 除权价² ≈ 1 (复权因子关系)
            try:
                forward_price = float(forward_row['收盘价'])
                backward_price = float(backward_row['收盘价'])
                no_adjust_price = float(no_adjust_row['收盘价'])
                
                # 检查价格是否合理（大于0）
                if any(price <= 0 for price in [forward_price, backward_price, no_adjust_price]):
                    results["price_anomalies"] += 1
                    continue
                
                # 计算复权因子（从除权价格推算）
                # 假设：前复权 = 除权 / 复权因子，后复权 = 除权 × 复权因子
                # 则：前复权 × 后复权 = 除权²
                expected_product = no_adjust_price * no_adjust_price
                actual_product = forward_price * backward_price
                
                # 计算误差百分比
                error_percentage = abs(expected_product - actual_product) / expected_product * 100
                
                # 分类准确度
                if error_percentage < 0.1:
                    accuracy_level = "high_accuracy"
                elif error_percentage < 1.0:
                    accuracy_level = "medium_accuracy"
                else:
                    accuracy_level = "low_accuracy"
                
                results["adjustment_accuracy"][accuracy_level] += 1
                
                if error_percentage > 1.0:  # 误差超过1%记录详情
                    code_errors.append({
                        "date": date,
                        "forward_price": forward_price,
                        "backward_price": backward_price,
                        "no_adjust_price": no_adjust_price,
                        "error_percentage": error_percentage
                    })
                
            except (ValueError, ZeroDivisionError) as e:
                results["calculation_errors"] += 1
                continue
        
        if code_errors:
            results["details"].append({
                "code": code,
                "errors": code_errors
            })
    
    return results


def generate_validation_report(consistency_results: dict, accuracy_results: dict):
    """生成验证报告"""
    log_message("📋 生成验证报告...")
    
    report = {
        "validation_time": datetime.now().isoformat(),
        "consistency_check": consistency_results,
        "accuracy_check": accuracy_results,
        "summary": {}
    }
    
    # 计算汇总指标
    if consistency_results["total_codes"] > 0:
        consistency_rate = consistency_results["consistent_codes"] / consistency_results["total_codes"] * 100
    else:
        consistency_rate = 0
    
    if accuracy_results["valid_samples"] > 0:
        high_accuracy_rate = accuracy_results["adjustment_accuracy"]["high_accuracy"] / accuracy_results["valid_samples"] * 100
        total_accuracy_count = sum(accuracy_results["adjustment_accuracy"].values())
        overall_accuracy_rate = total_accuracy_count / accuracy_results["valid_samples"] * 100 if accuracy_results["valid_samples"] > 0 else 0
    else:
        high_accuracy_rate = 0
        overall_accuracy_rate = 0
    
    report["summary"] = {
        "data_consistency_rate": round(consistency_rate, 2),
        "high_accuracy_rate": round(high_accuracy_rate, 2),
        "overall_accuracy_rate": round(overall_accuracy_rate, 2),
        "total_codes_checked": consistency_results["total_codes"],
        "total_samples_validated": accuracy_results["valid_samples"]
    }
    
    # 保存报告
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log_message(f"📄 验证报告已保存: {report_file}")
    
    return report


def print_summary_report(report: dict):
    """打印汇总报告"""
    log_message("=" * 60)
    log_message("📊 ETF数据验证汇总报告")
    log_message("=" * 60)
    
    summary = report["summary"]
    consistency = report["consistency_check"]
    accuracy = report["accuracy_check"]
    
    # 一致性检查结果
    log_message("🔍 日更与周更数据一致性:")
    log_message(f"  检查代码数量: {consistency['total_codes']}")
    log_message(f"  一致代码数量: {consistency['consistent_codes']}")
    log_message(f"  不一致代码数量: {consistency['inconsistent_codes']}")
    log_message(f"  一致性比例: {summary['data_consistency_rate']}%")
    
    if consistency['missing_in_daily'] > 0:
        log_message(f"  ⚠️ 日更缺失文件: {consistency['missing_in_daily']}")
    if consistency['missing_in_weekly'] > 0:
        log_message(f"  ⚠️ 周更缺失文件: {consistency['missing_in_weekly']}")
    
    log_message("")
    
    # 复权准确性检查结果
    log_message("🔬 三种复权数据准确性:")
    log_message(f"  抽样代码数量: {accuracy['total_samples']}")
    log_message(f"  有效样本数量: {accuracy['valid_samples']}")
    log_message(f"  高精度样本: {accuracy['adjustment_accuracy']['high_accuracy']} (误差<0.1%)")
    log_message(f"  中等精度样本: {accuracy['adjustment_accuracy']['medium_accuracy']} (误差0.1%-1%)")
    log_message(f"  低精度样本: {accuracy['adjustment_accuracy']['low_accuracy']} (误差>1%)")
    log_message(f"  高精度比例: {summary['high_accuracy_rate']}%")
    log_message(f"  整体可信度: {summary['overall_accuracy_rate']}%")
    
    if accuracy['price_anomalies'] > 0:
        log_message(f"  ⚠️ 价格异常: {accuracy['price_anomalies']} 个样本")
    if accuracy['calculation_errors'] > 0:
        log_message(f"  ⚠️ 计算错误: {accuracy['calculation_errors']} 个样本")
    
    log_message("")
    
    # 总体评估
    log_message("🏁 总体评估:")
    if summary['data_consistency_rate'] >= 95 and summary['high_accuracy_rate'] >= 90:
        log_message("  ✅ 数据质量优秀：一致性和准确性都很高")
    elif summary['data_consistency_rate'] >= 90 and summary['high_accuracy_rate'] >= 80:
        log_message("  ✅ 数据质量良好：基本满足使用要求")
    elif summary['data_consistency_rate'] >= 80 or summary['high_accuracy_rate'] >= 70:
        log_message("  ⚠️ 数据质量一般：需要注意部分异常数据")
    else:
        log_message("  ❌ 数据质量较差：建议检查数据处理流程")
    
    log_message("=" * 60)


def main():
    """主函数"""
    log_message("🚀 ETF数据验证程序启动")
    log_message(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查目录是否存在
    if not os.path.exists(DAILY_DIR):
        log_message(f"❌ 日更目录不存在: {DAILY_DIR}", "ERROR")
        return False
    
    if not os.path.exists(WEEKLY_DIR):
        log_message(f"❌ 周更目录不存在: {WEEKLY_DIR}", "ERROR")
        return False
    
    try:
        # 1. 验证日更和周更数据一致性
        consistency_results = compare_daily_weekly_consistency()
        
        log_message("")
        
        # 2. 验证三种复权数据准确性
        accuracy_results = validate_three_adjustments_accuracy()
        
        log_message("")
        
        # 3. 生成验证报告
        report = generate_validation_report(consistency_results, accuracy_results)
        
        # 4. 打印汇总报告
        print_summary_report(report)
        
        log_message(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_message("🎉 数据验证完成！")
        
        return True
        
    except Exception as e:
        log_message(f"❌ 验证过程中出现异常: {e}", "ERROR")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 