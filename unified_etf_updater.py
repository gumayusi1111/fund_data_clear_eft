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
            
            # 只添加数据文件，不包含Python脚本
            data_patterns = [
                "ETF日更/0_ETF日K(前复权)/*.csv",
                "ETF日更/0_ETF日K(后复权)/*.csv", 
                "ETF日更/0_ETF日K(除权)/*.csv",
                "ETF周更/0_ETF日K(前复权)/*.csv",
                "ETF周更/0_ETF日K(后复权)/*.csv",
                "ETF周更/0_ETF日K(除权)/*.csv",
                "ETF市场状况/etf_market_status.json"
            ]
            
            added_files = []
            
            for pattern in data_patterns:
                add_result = subprocess.run(
                    ["git", "add", pattern],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True
                )
                
                if add_result.returncode == 0:
                    added_files.append(pattern)
                    self.logger.info(f"✅ 已添加数据文件: {pattern}")
                else:
                    # 如果文件不存在或没有变化，不报错
                    if "did not match any files" not in add_result.stderr:
                        self.logger.warning(f"⚠️ 添加文件失败: {pattern} - {add_result.stderr}")
            
            if not added_files:
                self.logger.info("ℹ️ 没有数据文件需要提交（可能都没有变化）")
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
        """执行日更流程（智能跳过）"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行ETF日更流程（智能检查）")
        self.logger.info("=" * 50)
        try:
            daily_script = self.project_root / "ETF日更" / "auto_daily_sync.py"
            if not daily_script.exists():
                self.logger.error(f"日更脚本不存在: {daily_script}")
                return False, "脚本不存在"
            daily_dir = self.project_root / "ETF日更"
            cmd = [sys.executable, "auto_daily_sync.py"]
            result = subprocess.run(
                cmd,
                cwd=str(daily_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            output = result.stdout + result.stderr
            if "没有找到今天的文件" in output or "未找到任何文件" in output:
                self.logger.info("📅 今天无新数据，智能跳过日更")
                return False, "无新数据"
            if "所有文件都已是最新" in output or "无需下载" in output:
                self.logger.info("📅 日更数据已是最新，智能跳过")
                return False, "已是最新"
            if result.returncode == 0 and ("处理完成" in output or "下载完成" in output or "合并完成" in output):
                self.logger.info("✅ ETF日更完成（有新数据）")
                return True, "有新数据"
            else:
                self.logger.error("❌ ETF日更失败")
                if result.stderr:
                    self.logger.error(f"错误: {result.stderr[:200]}...")
                return False, "执行失败"
        except Exception as e:
            self.logger.error(f"执行日更时发生异常: {str(e)}")
            return False, f"异常: {str(e)}"

    def run_weekly_update(self):
        """执行周更流程（智能跳过）"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行ETF周更流程（智能检查）")
        self.logger.info("=" * 50)
        try:
            weekly_script = self.project_root / "ETF周更" / "etf_auto_sync.py"
            if not weekly_script.exists():
                self.logger.error(f"周更脚本不存在: {weekly_script}")
                return False, "脚本不存在"
            weekly_dir = self.project_root / "ETF周更"
            cmd = [sys.executable, "etf_auto_sync.py"]
            result = subprocess.run(
                cmd,
                cwd=str(weekly_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            output = result.stdout + result.stderr
            if "所有文件都已是最新，无需下载" in output:
                self.logger.info("📊 周更压缩包无变化，智能跳过")
                return False, "无变化"
            if "未找到" in output and "月" in output:
                self.logger.info("📊 未找到当前月份压缩包，智能跳过")
                return False, "无当月数据"
            if result.returncode == 0 and ("数据同步完成" in output or "合并完成" in output or "下载完成" in output):
                self.logger.info("✅ ETF周更完成（有新数据）")
                return True, "有新数据"
            else:
                self.logger.error("❌ ETF周更失败")
                if result.stderr:
                    self.logger.error(f"错误: {result.stderr[:200]}...")
                return False, "执行失败"
        except Exception as e:
            self.logger.error(f"执行周更时发生异常: {str(e)}")
            return False, f"异常: {str(e)}"

    def run_market_status_check(self, daily_has_new_data: bool):
        """执行ETF市场状况监控（依赖日更）"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行ETF市场状况监控（智能检查）")
        self.logger.info("=" * 50)
        if not daily_has_new_data:
            self.logger.info("📊 日更无新数据，智能跳过市场状况检查")
            return False, "依赖日更跳过"
        try:
            market_script = self.project_root / "ETF市场状况" / "market_status_monitor.py"
            if not market_script.exists():
                self.logger.error(f"市场状况监控脚本不存在: {market_script}")
                return False, "脚本不存在"
            market_dir = self.project_root / "ETF市场状况"
            cmd = [sys.executable, "market_status_monitor.py"]
            result = subprocess.run(
                cmd,
                cwd=str(market_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            output = result.stdout + result.stderr
            if result.returncode == 0 and ("报告已更新" in output or "监控完成" in output):
                self.logger.info("✅ ETF市场状况监控完成（有新数据）")
                return True, "有新数据"
            else:
                self.logger.error("❌ ETF市场状况监控失败")
                if result.stderr:
                    self.logger.error(f"错误: {result.stderr[:200]}...")
                return False, "执行失败"
        except Exception as e:
            self.logger.error(f"执行市场状况监控时发生异常: {str(e)}")
            return False, f"异常: {str(e)}"

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
        """执行完整更新流程（智能跳过无新数据的流程）"""
        start_time = datetime.now()
        self.logger.info("🚀 开始执行完整ETF数据更新流程（智能跳过无新数据）")
        results = {
            'daily': False,
            'weekly': False,
            'market_status': False
        }
        reasons = {}
        # 1. 执行日更
        daily_has_new, daily_reason = self.run_daily_update()
        results['daily'] = daily_has_new
        reasons['daily'] = daily_reason
        # 2. 执行周更
        weekly_has_new, weekly_reason = self.run_weekly_update()
        results['weekly'] = weekly_has_new
        reasons['weekly'] = weekly_reason
        # 3. 市场状况依赖日更
        market_has_new, market_reason = self.run_market_status_check(daily_has_new)
        results['market_status'] = market_has_new
        reasons['market_status'] = market_reason
        # 4. 数据库导入（只有有新数据才导入）
        if daily_has_new:
            self.logger.info("📥 日更有新数据，导入数据库...")
            self.run_database_import("daily")
        if weekly_has_new:
            self.logger.info("📥 周更有新数据，导入数据库...")
            self.run_database_import("weekly")
        if market_has_new:
            self.logger.info("📥 市场状况有新数据，导入数据库...")
            self.run_database_import("market_status")
        # 5. 只有有新数据才允许Git提交
        total_success = sum(results.values())
        if total_success > 0:
            self.logger.info("")
            git_success = self.auto_git_commit(results)
            if git_success:
                self.logger.info("✅ 数据更新和Git提交全部完成！")
            else:
                self.logger.warning("⚠️ 数据更新完成，但Git提交失败")
        else:
            self.logger.info("ℹ️ 没有成功的更新，跳过Git提交")
        # 总结报告
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
        for k in results:
            self.logger.info(f"  {k}: {'✅ 有新数据' if results[k] else '⏭️ 跳过/无新数据'} ({reasons[k]})")
        self.logger.info(f"整体有新数据模块数: {total_success}/3")
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