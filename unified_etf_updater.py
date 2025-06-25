#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一ETF更新器
一键执行日更和周更的ETF数据同步
支持test模式验证系统状态
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入配置
from config.logger_config import setup_system_logger
from config.hash_manager import HashManager

class UnifiedETFUpdater:
    def __init__(self):
        """初始化统一更新器"""
        self.project_root = PROJECT_ROOT
        self.logger = setup_system_logger()
        
        # 加载配置
        config_path = self.project_root / "config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 初始化哈希管理器 - 使用绝对路径
        hash_manager_path = self.project_root / "config" / "hash_manager.py"
        hash_config_path = self.project_root / "config" / "file_hashes.json"
        self.hash_manager = HashManager(str(hash_config_path))
        
        self.logger.info("统一ETF更新器初始化完成")
        
    def run_daily_update(self):
        """执行日更流程"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行ETF日更流程")
        self.logger.info("=" * 50)
        
        try:
            # 执行日更同步脚本
            daily_script = self.project_root / "ETF日更" / "auto_daily_sync.py"
            
            if not daily_script.exists():
                self.logger.error(f"日更脚本不存在: {daily_script}")
                return False
                
            # 切换到日更目录执行脚本
            daily_dir = self.project_root / "ETF日更"
            
            cmd = [sys.executable, "auto_daily_sync.py"]
            result = subprocess.run(
                cmd,
                cwd=str(daily_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.logger.info("✅ ETF日更完成")
                self.logger.info("日更输出:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
                return True
            else:
                self.logger.error("❌ ETF日更失败")
                self.logger.error("错误输出:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.logger.error(f"  {line}")
                        
                # 可能是非交易日或网络问题
                if "没有找到" in result.stderr or "not found" in result.stderr.lower():
                    self.logger.warning("⚠️  可能原因: 今天是非交易日或数据暂未更新")
                
                return False
                
        except Exception as e:
            self.logger.error(f"执行日更时发生异常: {str(e)}")
            return False
    
    def run_weekly_update(self):
        """执行周更流程"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行ETF周更流程")
        self.logger.info("=" * 50)
        
        try:
            # 执行周更同步脚本
            weekly_script = self.project_root / "ETF周更" / "etf_auto_sync.py"
            
            if not weekly_script.exists():
                self.logger.error(f"周更脚本不存在: {weekly_script}")
                return False
                
            # 切换到周更目录执行脚本
            weekly_dir = self.project_root / "ETF周更"
            
            cmd = [sys.executable, "etf_auto_sync.py"]
            result = subprocess.run(
                cmd,
                cwd=str(weekly_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.logger.info("✅ ETF周更完成")
                self.logger.info("周更输出:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
                return True
            else:
                self.logger.error("❌ ETF周更失败")
                self.logger.error("错误输出:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.logger.error(f"  {line}")
                return False
                
        except Exception as e:
            self.logger.error(f"执行周更时发生异常: {str(e)}")
            return False
    
    def run_market_status_check(self):
        """执行ETF市场状况监控"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行ETF市场状况监控")
        self.logger.info("=" * 50)
        
        try:
            # 执行市场状况监控脚本
            market_script = self.project_root / "ETF市场状况" / "market_status_monitor.py"
            
            if not market_script.exists():
                self.logger.error(f"市场状况监控脚本不存在: {market_script}")
                return False
                
            # 切换到市场状况目录执行脚本
            market_dir = self.project_root / "ETF市场状况"
            
            cmd = [sys.executable, "market_status_monitor.py"]
            result = subprocess.run(
                cmd,
                cwd=str(market_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.logger.info("✅ ETF市场状况监控完成")
                
                # 解析输出中的关键统计信息
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if any(keyword in line for keyword in ['活跃ETF', '正常ETF', '可能暂停', '可能退市', '数据异常']):
                        self.logger.info(f"  📊 {line.strip()}")
                    elif '可能已退市的ETF' in line:
                        self.logger.info(f"  🔴 {line.strip()}")
                        
                return True
            else:
                self.logger.error("❌ ETF市场状况监控失败")
                self.logger.error("错误输出:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.logger.error(f"  {line}")
                return False
                
        except Exception as e:
            self.logger.error(f"执行市场状况监控时发生异常: {str(e)}")
            return False
    
    def test_system_status(self):
        """测试系统状态"""
        self.logger.info("🔍 开始系统状态测试")
        
        # 检查目录结构
        required_dirs = [
            "ETF日更",
            "ETF周更", 
            "ETF市场状况",
            "config",
            "logs",
            "scripts"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                self.logger.info(f"✅ 目录存在: {dir_name}")
            else:
                self.logger.error(f"❌ 目录缺失: {dir_name}")
        
        # 检查关键文件
        required_files = [
            "config/config.json",
            "config/hash_manager.py",
            "ETF日更/auto_daily_sync.py",
            "ETF周更/etf_auto_sync.py",
            "ETF市场状况/market_status_monitor.py"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.logger.info(f"✅ 文件存在: {file_path}")
            else:
                self.logger.error(f"❌ 文件缺失: {file_path}")
        
        # 检查配置文件
        try:
            self.logger.info(f"✅ 配置加载成功，包含 {len(self.config)} 个配置项")
        except Exception as e:
            self.logger.error(f"❌ 配置加载失败: {e}")
        
        # 检查日志系统
        log_file = "etf_sync.log"
        log_path = self.project_root / "logs" / "system" / log_file
        
        if log_path.exists():
            self.logger.info(f"✅ 统一日志文件存在: {log_file}")
        else:
            self.logger.info(f"ℹ️  统一日志文件将自动创建: {log_file}")
        
        self.logger.info("🔍 系统状态测试完成")
    
    def run_full_update(self):
        """执行完整更新流程"""
        start_time = datetime.now()
        self.logger.info("🚀 开始执行完整ETF数据更新流程")
        
        results = {
            'daily': False,
            'weekly': False,
            'market_status': False
        }
        
        # 1. 执行日更
        results['daily'] = self.run_daily_update()
        
        # 2. 执行周更
        results['weekly'] = self.run_weekly_update()
        
        # 3. 执行市场状况监控
        results['market_status'] = self.run_market_status_check()
        
        # 生成总结报告
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("=" * 60)
        self.logger.info("📊 ETF数据更新完成总结")
        self.logger.info("=" * 60)
        self.logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"总耗时: {duration}")
        self.logger.info("")
        self.logger.info("各模块执行结果:")
        self.logger.info(f"  📈 日更流程: {'✅ 成功' if results['daily'] else '❌ 失败'}")
        self.logger.info(f"  📊 周更流程: {'✅ 成功' if results['weekly'] else '❌ 失败'}")
        self.logger.info(f"  🔍 市场状况监控: {'✅ 成功' if results['market_status'] else '❌ 失败'}")
        
        total_success = sum(results.values())
        self.logger.info(f"")
        self.logger.info(f"整体成功率: {total_success}/3 ({total_success/3*100:.1f}%)")
        
        if total_success == 3:
            self.logger.info("🎉 所有流程执行成功！")
        elif total_success >= 2:
            self.logger.info("⚠️  大部分流程执行成功，请检查失败项")
        else:
            self.logger.error("❌ 大部分流程执行失败，请检查系统状态")
        
        return results

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 测试模式
        updater = UnifiedETFUpdater()
        updater.test_system_status()
    else:
        # 正常更新模式
        updater = UnifiedETFUpdater()
        updater.run_full_update()

if __name__ == "__main__":
    main() 