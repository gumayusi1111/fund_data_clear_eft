#!/usr/bin/env python3
"""
ETF 统一更新脚本
1. 自动执行周更新（如果有新数据）
2. 自动执行日更新（每天执行）
3. 使用分离的日志系统
4. 统一的错误处理和状态报告
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

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
    
    # 设置统一更新日志
    logger = setup_logger("etf_unified", "general")
except ImportError as e:
    print(f"警告：无法导入日志配置: {e}")
    logger = None


def load_config():
    """加载配置文件"""
    config_path = os.path.join(config_dir, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}")
        return {}


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


def run_weekly_update() -> bool:
    """运行周更新"""
    log_message("🗓️ 开始执行周更新...")
    
    try:
        config = load_config()
        weekly_dir = config.get("baidu_netdisk", {}).get("weekly_local_path", "./ETF周更")
        
        # 切换到周更目录执行脚本
        weekly_script = os.path.join(weekly_dir, "etf_auto_sync.py")
        
        if not os.path.exists(weekly_script):
            log_message(f"❌ 周更脚本不存在: {weekly_script}", "ERROR")
            return False
        
        # 执行周更脚本
        result = subprocess.run(
            ["python", "etf_auto_sync.py"],
            cwd=weekly_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            log_message("✅ 周更新执行完成")
            # 记录重要输出
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # 显示最后10行重要信息
                    if any(keyword in line for keyword in ['✓', '完成', '成功', '找到', '处理']):
                        log_message(f"  {line}")
            return True
        else:
            log_message(f"❌ 周更新执行失败: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log_message("❌ 周更新执行超时", "ERROR")
        return False
    except Exception as e:
        log_message(f"❌ 周更新执行异常: {e}", "ERROR")
        return False


def run_daily_update() -> bool:
    """运行日更新"""
    log_message("📅 开始执行日更新...")
    
    try:
        config = load_config()
        daily_dir = config.get("baidu_netdisk", {}).get("daily_local_path", "./ETF日更")
        
        # 切换到日更目录执行脚本
        daily_script = os.path.join(daily_dir, "auto_daily_sync.py")
        
        if not os.path.exists(daily_script):
            log_message(f"❌ 日更脚本不存在: {daily_script}", "ERROR")
            return False
        
        # 执行日更脚本
        result = subprocess.run(
            ["python", "auto_daily_sync.py", "--mode", "daily"],
            cwd=daily_dir,
            capture_output=True,
            text=True,
            timeout=900  # 15分钟超时
        )
        
        if result.returncode == 0:
            log_message("✅ 日更新执行完成")
            # 记录重要输出
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # 显示最后10行重要信息
                    if any(keyword in line for keyword in ['✓', '完成', '成功', '下载', '处理']):
                        log_message(f"  {line}")
            return True
        else:
            log_message(f"⚠️ 日更新执行结果: {result.stderr}", "WARNING")
            # 日更新失败不一定是错误（可能是今天没有新数据）
            if "没有今天的文件" in result.stderr or "非交易日" in result.stderr:
                log_message("ℹ️ 今天没有新数据，这是正常情况")
                return True
            return False
            
    except subprocess.TimeoutExpired:
        log_message("❌ 日更新执行超时", "ERROR")
        return False
    except Exception as e:
        log_message(f"❌ 日更新执行异常: {e}", "ERROR")
        return False


def check_system_status() -> dict:
    """检查系统状态"""
    log_message("🔍 检查系统状态...")
    
    config = load_config()
    status = {
        "config_loaded": bool(config),
        "weekly_dir_exists": False,
        "daily_dir_exists": False,
        "weekly_script_exists": False,
        "daily_script_exists": False
    }
    
    if config:
        # 检查目录和脚本
        weekly_dir = config.get("baidu_netdisk", {}).get("weekly_local_path", "./ETF周更")
        daily_dir = config.get("baidu_netdisk", {}).get("daily_local_path", "./ETF日更")
        
        status["weekly_dir_exists"] = os.path.exists(weekly_dir)
        status["daily_dir_exists"] = os.path.exists(daily_dir)
        status["weekly_script_exists"] = os.path.exists(os.path.join(weekly_dir, "etf_auto_sync.py"))
        status["daily_script_exists"] = os.path.exists(os.path.join(daily_dir, "auto_daily_sync.py"))
    
    # 输出状态报告
    log_message(f"  配置文件: {'✅' if status['config_loaded'] else '❌'}")
    log_message(f"  周更目录: {'✅' if status['weekly_dir_exists'] else '❌'}")
    log_message(f"  日更目录: {'✅' if status['daily_dir_exists'] else '❌'}")
    log_message(f"  周更脚本: {'✅' if status['weekly_script_exists'] else '❌'}")
    log_message(f"  日更脚本: {'✅' if status['daily_script_exists'] else '❌'}")
    
    return status


def main():
    """主函数"""
    log_message("🚀 ETF统一更新程序启动")
    log_message(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查系统状态
    status = check_system_status()
    
    if not all([status["config_loaded"], status["weekly_dir_exists"], 
                status["daily_dir_exists"], status["weekly_script_exists"], 
                status["daily_script_exists"]]):
        log_message("❌ 系统状态检查失败，请确保所有组件都已正确设置", "ERROR")
        return False
    
    log_message("✅ 系统状态检查通过")
    
    # 总体结果统计
    results = {
        "weekly": False,
        "daily": False
    }
    
    try:
        # 1. 执行周更新（顺带更新，不管有没有新数据）
        log_message("=" * 50)
        results["weekly"] = run_weekly_update()
        
        # 2. 执行日更新（每天都要执行）
        log_message("=" * 50)
        results["daily"] = run_daily_update()
        
        # 3. 汇总结果
        log_message("=" * 50)
        log_message("📊 更新结果汇总:")
        log_message(f"  周更新: {'✅ 成功' if results['weekly'] else '❌ 失败'}")
        log_message(f"  日更新: {'✅ 成功' if results['daily'] else '❌ 失败'}")
        
        if all(results.values()):
            log_message("🎉 所有更新任务完成！")
            return True
        elif results["daily"]:
            log_message("⚠️ 日更新成功，周更新失败（可能无新数据）")
            return True
        else:
            log_message("❌ 更新过程中出现问题")
            return False
            
    except KeyboardInterrupt:
        log_message("⚠️ 用户中断操作", "WARNING")
        return False
    except Exception as e:
        log_message(f"❌ 执行过程中出现异常: {e}", "ERROR")
        return False


def test_system():
    """测试系统连接和配置"""
    log_message("🔧 执行系统测试...")
    
    # 检查系统状态
    status = check_system_status()
    
    if not status["config_loaded"]:
        log_message("❌ 测试失败：配置文件加载失败", "ERROR")
        return False
    
    # 测试周更连接
    log_message("📡 测试周更连接...")
    try:
        config = load_config()
        weekly_dir = config.get("baidu_netdisk", {}).get("weekly_local_path", "./ETF周更")
        
        result = subprocess.run(
            ["python", "etf_auto_sync.py", "test"],
            cwd=weekly_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        weekly_test_ok = result.returncode == 0
        log_message(f"  周更连接: {'✅ 正常' if weekly_test_ok else '❌ 异常'}")
        
    except Exception as e:
        log_message(f"  周更连接: ❌ 测试失败 - {e}")
        weekly_test_ok = False
    
    # 测试日更连接
    log_message("📡 测试日更连接...")
    try:
        daily_dir = config.get("baidu_netdisk", {}).get("daily_local_path", "./ETF日更")
        
        result = subprocess.run(
            ["python", "auto_daily_sync.py", "--mode", "test"],
            cwd=daily_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        daily_test_ok = result.returncode == 0
        log_message(f"  日更连接: {'✅ 正常' if daily_test_ok else '❌ 异常'}")
        
    except Exception as e:
        log_message(f"  日更连接: ❌ 测试失败 - {e}")
        daily_test_ok = False
    
    # 汇总测试结果
    log_message("📋 测试结果汇总:")
    log_message(f"  系统配置: {'✅' if all(status.values()) else '❌'}")
    log_message(f"  周更连接: {'✅' if weekly_test_ok else '❌'}")
    log_message(f"  日更连接: {'✅' if daily_test_ok else '❌'}")
    
    all_ok = all(status.values()) and weekly_test_ok and daily_test_ok
    log_message(f"🏁 总体状态: {'✅ 系统正常' if all_ok else '❌ 需要检查'}")
    
    return all_ok


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF统一更新脚本')
    parser.add_argument('--mode', choices=['update', 'test'], default='update',
                        help='运行模式: update(执行更新), test(测试系统)')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        success = test_system()
    else:
        success = main()
    
    sys.exit(0 if success else 1) 