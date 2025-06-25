#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF生命周期管理器
负责管理ETF的上市、下市、状态变更等生命周期事件
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from config.logger_config import setup_lifecycle_logger, get_report_paths

class ETFLifecycleManager:
    """ETF生命周期管理器"""
    
    def __init__(self, config_path=None):
        """初始化ETF生命周期管理器"""
        if config_path is None:
            # 配置文件在同一目录下
            config_path = script_dir / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 使用专用的生命周期日志记录器
        self.logger = setup_lifecycle_logger()
        
        # 设置报告目录路径
        self.report_paths = get_report_paths()
        self.lifecycle_reports_dir = self.report_paths['lifecycle_reports']
        self.lifecycle_reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("ETF生命周期管理器初始化完成")
        
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            default_config = {
                "etf_lifecycle": {
                    "newly_listed": [],
                    "delisted": [],
                    "suspended": [],
                    "last_updated": ""
                }
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config):
        """保存配置文件"""
        config["etf_lifecycle"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"配置已保存到: {self.config_path}")
    
    def add_newly_listed_etf(self, etf_code, etf_name, listing_date, note=""):
        """添加新上市ETF"""
        etf_info = {
            "code": etf_code,
            "name": etf_name,
            "listing_date": listing_date,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
            "note": note
        }
        
        # 检查是否已存在
        newly_listed = self.config.get("etf_lifecycle", {}).get("newly_listed", [])
        for etf in newly_listed:
            if etf["code"] == etf_code:
                self.logger.warning(f"ETF {etf_code} 已在新上市列表中")
                return False
        
        # 添加到配置
        if "etf_lifecycle" not in self.config:
            self.config["etf_lifecycle"] = {"newly_listed": [], "delisted": [], "suspended": []}
        
        self.config["etf_lifecycle"]["newly_listed"].append(etf_info)
        self._save_config(self.config)
        
        self.logger.info(f"新增上市ETF: {etf_code} - {etf_name}, 上市日期: {listing_date}")
        return True
    
    def add_delisted_etf(self, etf_code, etf_name, delisting_date, reason=""):
        """添加下市ETF"""
        etf_info = {
            "code": etf_code,
            "name": etf_name,
            "delisting_date": delisting_date,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
            "reason": reason
        }
        
        # 检查是否已存在
        delisted = self.config.get("etf_lifecycle", {}).get("delisted", [])
        for etf in delisted:
            if etf["code"] == etf_code:
                self.logger.warning(f"ETF {etf_code} 已在下市列表中")
                return False
        
        # 添加到配置
        if "etf_lifecycle" not in self.config:
            self.config["etf_lifecycle"] = {"newly_listed": [], "delisted": [], "suspended": []}
        
        self.config["etf_lifecycle"]["delisted"].append(etf_info)
        
        # 如果该ETF在新上市列表中，从新上市列表移除
        newly_listed = self.config["etf_lifecycle"]["newly_listed"]
        self.config["etf_lifecycle"]["newly_listed"] = [
            etf for etf in newly_listed if etf["code"] != etf_code
        ]
        
        self._save_config(self.config)
        
        self.logger.info(f"新增下市ETF: {etf_code} - {etf_name}, 下市日期: {delisting_date}")
        return True
    
    def batch_add_newly_listed_etfs(self, etf_list):
        """批量添加新上市ETF
        
        Args:
            etf_list: ETF列表，格式为 [{"code": "159228", "name": "长城中证红利低波100ETF", "listing_date": "2025-06-18"}, ...]
        """
        added_count = 0
        for etf in etf_list:
            if self.add_newly_listed_etf(
                etf["code"], 
                etf["name"], 
                etf["listing_date"], 
                etf.get("note", "")
            ):
                added_count += 1
        
        self.logger.info(f"批量添加完成，共添加 {added_count} 个新上市ETF")
        return added_count
    
    def get_newly_listed_etfs(self):
        """获取新上市ETF列表"""
        return self.config.get("etf_lifecycle", {}).get("newly_listed", [])
    
    def get_delisted_etfs(self):
        """获取下市ETF列表"""
        return self.config.get("etf_lifecycle", {}).get("delisted", [])
    
    def get_etf_status(self, etf_code):
        """获取ETF状态"""
        # 检查是否在新上市列表
        for etf in self.get_newly_listed_etfs():
            if etf["code"] == etf_code:
                return "newly_listed", etf
        
        # 检查是否在下市列表
        for etf in self.get_delisted_etfs():
            if etf["code"] == etf_code:
                return "delisted", etf
        
        return "normal", None
    
    def generate_lifecycle_report(self):
        """生成生命周期报告"""
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "newly_listed_count": len(self.get_newly_listed_etfs()),
            "delisted_count": len(self.get_delisted_etfs()),
            "newly_listed_etfs": self.get_newly_listed_etfs(),
            "delisted_etfs": self.get_delisted_etfs()
        }
        
        # 保存报告到生命周期报告目录
        report_filename = f"etf_lifecycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.lifecycle_reports_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"生命周期报告已生成: {report_path}")
        return report, report_path

def quick_add_june_2025_etfs():
    """快速添加2025年6月新上市的ETF"""
    manager = ETFLifecycleManager()
    
    june_2025_etfs = [
        {"code": "159228", "name": "长城中证红利低波100ETF", "listing_date": "2025-06-18"},
        {"code": "159240", "name": "天弘中证A500增强策略ETF", "listing_date": "2025-06-17"},
        {"code": "159245", "name": "富国国证港股通消费主题ETF", "listing_date": "2025-06-19"},
        {"code": "561770", "name": "博时中证A100ETF", "listing_date": "2025-06-24"},
        {"code": "562050", "name": "华宝中证制药ETF", "listing_date": "2025-06-19"},
        {"code": "588270", "name": "易方达上证科创板200ETF", "listing_date": "2025-06-16"},
        {"code": "589180", "name": "汇添富上证科创板新材料ETF", "listing_date": "2025-06-16"}
    ]
    
    return manager.batch_add_newly_listed_etfs(june_2025_etfs)

def main():
    """测试生命周期管理器"""
    print("🧪 测试ETF生命周期管理器...")
    
    manager = ETFLifecycleManager()
    
    # 显示当前状态
    newly_listed = manager.get_newly_listed_etfs()
    delisted = manager.get_delisted_etfs()
    
    print(f"\n📊 当前生命周期状态:")
    print(f"新上市ETF: {len(newly_listed)} 个")
    for etf in newly_listed:
        print(f"  • {etf['code']} - {etf['name']} (上市: {etf['listing_date']})")
    
    print(f"已下市ETF: {len(delisted)} 个")
    for etf in delisted:
        print(f"  • {etf['code']} - {etf['name']} (下市: {etf['delisting_date']})")
    
    print("\n✅ 生命周期管理器测试完成！")


if __name__ == "__main__":
    main() 