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

# 导入数据库模块
DATABASE_IMPORT_AVAILABLE = False
DailyDataImporter = None
WeeklyDataImporter = None
MarketStatusImporter = None

def load_database_modules():
    """动态加载数据库导入模块"""
    global DATABASE_IMPORT_AVAILABLE, DailyDataImporter, WeeklyDataImporter, MarketStatusImporter
    try:
        from ETF_database.importers.daily_importer import DailyDataImporter as _DailyDataImporter
        from ETF_database.importers.weekly_importer import WeeklyDataImporter as _WeeklyDataImporter
        from ETF_database.importers.market_status_importer import MarketStatusImporter as _MarketStatusImporter
        
        DailyDataImporter = _DailyDataImporter
        WeeklyDataImporter = _WeeklyDataImporter
        MarketStatusImporter = _MarketStatusImporter
        DATABASE_IMPORT_AVAILABLE = True
        return True
    except ImportError as e:
        print(f"⚠️ 数据库导入模块不可用: {e}")
        return False

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
        
        # 数据库导入配置
        self.db_config = self.config.get('database_import', {})
        self.auto_import_enabled = self.db_config.get('enabled', True)
        
        # 动态加载数据库模块
        db_loaded = load_database_modules()
        
        self.logger.info("统一ETF更新器初始化完成")
        if db_loaded and self.auto_import_enabled:
            self.logger.info("✅ 数据库自动导入已启用")
        elif db_loaded and not self.auto_import_enabled:
            self.logger.info("ℹ️ 数据库自动导入已禁用")
        else:
            self.logger.warning("⚠️ 数据库导入模块不可用")
        
    def auto_git_commit(self, success_modules):
        """自动提交Git更新"""
        # 检查是否启用Git自动提交
        git_config = self.config.get('git_auto_commit', {})
        if not git_config.get('enabled', False):
            self.logger.info("ℹ️ Git自动提交已禁用，跳过")
            return True
            
        self.logger.info("=" * 50)
        self.logger.info("开始自动Git提交")
        self.logger.info("=" * 50)
        
        try:
            # 检查是否是Git仓库
            result = subprocess.run(
                ["git", "status"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.warning("⚠️ 当前目录不是Git仓库，跳过自动提交")
                return False
            
            # 检查是否有变更
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                self.logger.info("ℹ️ 没有文件变更，跳过提交")
                return True
            
            # 显示变更的文件
            self.logger.info("📄 检测到以下文件变更:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    self.logger.info(f"   {line}")
            
            # 添加所有变更文件
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if add_result.returncode != 0:
                self.logger.error(f"❌ Git add 失败: {add_result.stderr}")
                return False
            
            # 生成提交信息
            success_count = len([m for m in success_modules.values() if m])
            total_count = len(success_modules)
            
            commit_prefix = git_config.get('commit_message_prefix', '数据自动更新')
            commit_msg = f"{commit_prefix} - 成功率:{success_count}/{total_count}"
            
            # 添加时间戳（如果配置启用）
            if git_config.get('include_timestamp', True):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                commit_msg = f"{commit_prefix} {timestamp} - 成功率:{success_count}/{total_count}"
            
            # 添加详细信息
            if success_modules.get('daily'):
                commit_msg += "\n✅ 日更数据已更新"
            if success_modules.get('weekly'):
                commit_msg += "\n✅ 周更数据已更新"
            if success_modules.get('market_status'):
                commit_msg += "\n✅ 市场状况已更新"
            
            # 执行提交
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if commit_result.returncode == 0:
                self.logger.info("✅ Git提交成功")
                self.logger.info(f"📝 提交信息: {commit_msg.split(chr(10))[0]}")
                
                # 根据配置决定是否推送到远程仓库
                if git_config.get('auto_push', True):
                    push_result = subprocess.run(
                        ["git", "push"],
                        cwd=str(self.project_root),
                        capture_output=True,
                        text=True
                    )
                    
                    if push_result.returncode == 0:
                        self.logger.info("✅ 推送到远程仓库成功")
                    else:
                        self.logger.warning("⚠️ 推送到远程仓库失败，但本地提交成功")
                        self.logger.warning(f"推送错误: {push_result.stderr}")
                else:
                    self.logger.info("ℹ️ 自动推送已禁用，仅本地提交")
                
                return True
            else:
                self.logger.error(f"❌ Git提交失败: {commit_result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"自动Git提交时发生异常: {str(e)}")
            return False
    
    def run_database_import(self, import_type: str, base_dir: str = None) -> bool:
        """执行数据库导入"""
        if not DATABASE_IMPORT_AVAILABLE:
            self.logger.warning("⚠️ 数据库导入模块不可用，跳过数据库导入")
            return False
        
        if not self.auto_import_enabled:
            self.logger.info("ℹ️ 数据库自动导入已禁用，跳过")
            return True
        
        self.logger.info(f"📊 开始执行{import_type}数据库导入...")
        
        try:
            if import_type == "daily":
                importer = DailyDataImporter()
                base_dir = base_dir or str(self.project_root / "ETF日更")
                # 只导入最近1天的数据（增量导入）
                results = importer.import_latest_data_only(base_dir, days_back=1)
                
            elif import_type == "weekly":
                importer = WeeklyDataImporter()
                base_dir = base_dir or str(self.project_root / "ETF周更")
                # 只导入最近1周的数据（增量导入）
                results = importer.import_latest_weekly_data(base_dir, weeks_back=1)
                
            elif import_type == "market_status":
                importer = MarketStatusImporter()
                json_file = str(self.project_root / "ETF市场状况" / "etf_market_status.json")
                results = {"market_status": importer.import_json_file(json_file)}
                
            else:
                self.logger.error(f"❌ 不支持的导入类型: {import_type}")
                return False
            
            # 检查导入结果
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            if success_count > 0:
                self.logger.info(f"✅ {import_type}数据库导入完成: {success_count}/{total_count}")
                return True
            else:
                self.logger.warning(f"⚠️ {import_type}数据库导入无更新: {success_count}/{total_count}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {import_type}数据库导入失败: {str(e)}")
            return False
        
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
                
                # 数据更新成功后，自动导入到数据库
                db_import_success = self.run_database_import("daily")
                if db_import_success:
                    self.logger.info("✅ 日更数据库导入完成")
                else:
                    self.logger.warning("⚠️ 日更数据库导入失败或无更新")
                
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
                
                # 数据更新成功后，自动导入到数据库
                db_import_success = self.run_database_import("weekly")
                if db_import_success:
                    self.logger.info("✅ 周更数据库导入完成")
                else:
                    self.logger.warning("⚠️ 周更数据库导入失败或无更新")
                
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
                
                # 市场状况更新成功后，自动导入到数据库
                db_import_success = self.run_database_import("market_status")
                if db_import_success:
                    self.logger.info("✅ 市场状况数据库导入完成")
                else:
                    self.logger.warning("⚠️ 市场状况数据库导入失败或无更新")
                        
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
        
        # 如果有任何模块成功执行，则进行自动Git提交
        if total_success > 0:
            self.logger.info("")
            git_success = self.auto_git_commit(results)
            if git_success:
                self.logger.info("✅ 数据更新和Git提交全部完成！")
            else:
                self.logger.warning("⚠️ 数据更新完成，但Git提交失败")
        else:
            self.logger.info("ℹ️ 没有成功的更新，跳过Git提交")
        
        return results

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一ETF更新器')
    parser.add_argument('--mode', choices=['update', 'test'], default='update',
                        help='运行模式: update(数据更新), test(系统测试)')
    parser.add_argument('--no-git', action='store_true',
                        help='禁用Git自动提交功能')
    parser.add_argument('--no-push', action='store_true',
                        help='禁用Git自动推送功能（仅本地提交）')
    
    args = parser.parse_args()
    
    updater = UnifiedETFUpdater()
    
    # 根据命令行参数临时修改配置
    if args.no_git:
        updater.config['git_auto_commit']['enabled'] = False
        updater.logger.info("🔧 已通过命令行参数禁用Git自动提交")
    
    if args.no_push:
        updater.config['git_auto_commit']['auto_push'] = False
        updater.logger.info("🔧 已通过命令行参数禁用Git自动推送")
    
    if args.mode == 'test':
        # 测试模式
        updater.test_system_status()
    else:
        # 正常更新模式
        updater.run_full_update()

if __name__ == "__main__":
    main() 