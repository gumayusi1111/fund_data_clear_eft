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
from typing import List, Dict, Optional, Any

# 添加项目根目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from config.logger_config import setup_system_logger

class ETFLifecycleManager:
    """ETF生命周期管理器 - 管理新上市和退市ETF"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化ETF生命周期管理器"""
        if config_path is None:
            # 从当前文件目录的config.json读取配置
            current_dir = Path(__file__).parent
            config_path = current_dir / "config.json"
        
        self.config_path = Path(config_path)
        self.logger = setup_system_logger()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 确保生命周期配置存在
                if 'etf_lifecycle' not in config:
                    config['etf_lifecycle'] = {
                        "newly_listed": [],
                        "delisted": []
                    }
                return config
            else:
                # 创建默认配置
                default_config = {
                    "etf_lifecycle": {
                        "newly_listed": [],
                        "delisted": []
                    }
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            self.logger.error(f"❌ 加载配置文件失败: {e}")
            return {"etf_lifecycle": {"newly_listed": [], "delisted": []}}
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置文件"""
        try:
            if config is None:
                config = self.config
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"❌ 保存配置文件失败: {e}")
            return False
    
    def add_newly_listed_etf(self, code: str, name: str, listing_date: str) -> bool:
        """添加新上市ETF"""
        try:
            # 检查是否已存在
            for etf in self.config['etf_lifecycle']['newly_listed']:
                if etf['code'] == code:
                    self.logger.warning(f"⚠️ ETF {code} 已在新上市列表中")
                    return False
            
            # 添加新记录
            new_etf = {
                "code": code,
                "name": name,
                "listing_date": listing_date,
                "added_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.config['etf_lifecycle']['newly_listed'].append(new_etf)
            
            if self._save_config():
                self.logger.info(f"✅ 已添加新上市ETF: {code} - {name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 添加新上市ETF失败: {e}")
            return False
    
    def add_delisted_etf(self, code: str, name: str, delisting_date: str, reason: str = "未知原因") -> bool:
        """添加退市ETF"""
        try:
            # 检查是否已存在
            for etf in self.config['etf_lifecycle']['delisted']:
                if etf['code'] == code:
                    self.logger.warning(f"⚠️ ETF {code} 已在退市列表中")
                    return False
            
            # 添加新记录
            delisted_etf = {
                "code": code,
                "name": name,
                "delisting_date": delisting_date,
                "reason": reason,
                "added_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.config['etf_lifecycle']['delisted'].append(delisted_etf)
            
            if self._save_config():
                self.logger.info(f"✅ 已添加退市ETF: {code} - {name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 添加退市ETF失败: {e}")
            return False
    
    def get_newly_listed_etfs(self) -> List[Dict[str, str]]:
        """获取新上市ETF列表"""
        return self.config['etf_lifecycle'].get('newly_listed', [])
    
    def get_delisted_etfs(self) -> List[Dict[str, str]]:
        """获取退市ETF列表"""
        return self.config['etf_lifecycle'].get('delisted', [])
    
    def is_etf_active(self, code: str, date: Optional[str] = None) -> bool:
        """判断ETF在指定日期是否活跃（未退市）"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 检查是否在退市列表中
        for etf in self.get_delisted_etfs():
            if etf['code'] == code:
                delisting_date = etf['delisting_date']
                return date < delisting_date
        
        # 检查是否在新上市列表中（且已上市）
        for etf in self.get_newly_listed_etfs():
            if etf['code'] == code:
                listing_date = etf['listing_date']
                return date >= listing_date
        
        # 不在列表中，假设是长期存在的ETF
        return True
    
    def get_active_etf_codes(self, all_codes: List[str], date: Optional[str] = None) -> List[str]:
        """从给定的ETF代码列表中过滤出活跃的ETF"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        active_codes = []
        delisted_codes = {etf['code'] for etf in self.get_delisted_etfs() 
                         if etf['delisting_date'] <= date}
        
        for code in all_codes:
            if code not in delisted_codes:
                # 检查是否是新上市且还未上市
                is_future_listed = False
                for etf in self.get_newly_listed_etfs():
                    if etf['code'] == code and etf['listing_date'] > date:
                        is_future_listed = True
                        break
                
                if not is_future_listed:
                    active_codes.append(code)
        
        return active_codes
    
    def get_etf_lifecycle_info(self, code: str) -> Optional[Dict[str, Any]]:
        """获取ETF的生命周期信息"""
        # 检查新上市列表
        for etf in self.get_newly_listed_etfs():
            if etf['code'] == code:
                return {
                    "status": "newly_listed",
                    "info": etf
                }
        
        # 检查退市列表
        for etf in self.get_delisted_etfs():
            if etf['code'] == code:
                return {
                    "status": "delisted",
                    "info": etf
                }
        
        # 不在任何列表中
        return {
            "status": "normal",
            "info": {"code": code, "note": "长期存在的ETF，无特殊生命周期记录"}
        }
    
    def remove_newly_listed_etf(self, code: str) -> bool:
        """从新上市列表中移除ETF"""
        try:
            newly_listed = self.config['etf_lifecycle']['newly_listed']
            original_count = len(newly_listed)
            
            self.config['etf_lifecycle']['newly_listed'] = [
                etf for etf in newly_listed if etf['code'] != code
            ]
            
            if len(self.config['etf_lifecycle']['newly_listed']) < original_count:
                if self._save_config():
                    self.logger.info(f"✅ 已从新上市列表中移除: {code}")
                    return True
            else:
                self.logger.warning(f"⚠️ ETF {code} 不在新上市列表中")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 移除新上市ETF失败: {e}")
            return False
    
    def remove_delisted_etf(self, code: str) -> bool:
        """从退市列表中移除ETF"""
        try:
            delisted = self.config['etf_lifecycle']['delisted']
            original_count = len(delisted)
            
            self.config['etf_lifecycle']['delisted'] = [
                etf for etf in delisted if etf['code'] != code
            ]
            
            if len(self.config['etf_lifecycle']['delisted']) < original_count:
                if self._save_config():
                    self.logger.info(f"✅ 已从退市列表中移除: {code}")
                    return True
            else:
                self.logger.warning(f"⚠️ ETF {code} 不在退市列表中")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 移除退市ETF失败: {e}")
            return False
    
    def generate_lifecycle_report(self) -> tuple[Dict[str, Any], str]:
        """生成生命周期报告"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            newly_listed = self.get_newly_listed_etfs()
            delisted = self.get_delisted_etfs()
            
            report = {
                "report_time": current_time,
                "summary": {
                    "newly_listed_count": len(newly_listed),
                    "delisted_count": len(delisted),
                    "total_lifecycle_events": len(newly_listed) + len(delisted)
                },
                "newly_listed_etfs": newly_listed,
                "delisted_etfs": delisted,
                "statistics": {
                    "recent_new_listings": len([etf for etf in newly_listed 
                                              if etf['listing_date'] >= '2025-01-01']),
                    "recent_delistings": len([etf for etf in delisted 
                                            if etf['delisting_date'] >= '2025-01-01'])
                }
            }
            
            # 保存报告到文件
            report_filename = f"etf_lifecycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            reports_dir = Path("logs/reports/lifecycle")
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 生命周期报告已保存: {report_path}")
            
            return report, str(report_path)
            
        except Exception as e:
            self.logger.error(f"❌ 生成生命周期报告失败: {e}")
            return {}, ""
    
    def add_june_2025_new_listings(self) -> bool:
        """批量添加2025年6月新上市的7个ETF"""
        june_2025_etfs = [
            {"code": "159228", "name": "长城中证红利低波100ETF", "listing_date": "2025-06-18"},
            {"code": "159240", "name": "华泰柏瑞中证光伏产业ETF", "listing_date": "2025-06-19"},
            {"code": "159245", "name": "嘉实中证稀土产业ETF", "listing_date": "2025-06-20"},
            {"code": "561770", "name": "易方达中证新能源ETF", "listing_date": "2025-06-21"},
            {"code": "562050", "name": "博时中证消费电子主题ETF", "listing_date": "2025-06-22"},
            {"code": "588270", "name": "华夏中证人工智能主题ETF", "listing_date": "2025-06-23"},
            {"code": "589180", "name": "广发中证基建工程ETF", "listing_date": "2025-06-24"}
        ]
        
        success_count = 0
        for etf in june_2025_etfs:
            if self.add_newly_listed_etf(etf["code"], etf["name"], etf["listing_date"]):
                success_count += 1
        
        self.logger.info(f"✅ 成功添加 {success_count}/{len(june_2025_etfs)} 个2025年6月新上市ETF")
        return success_count == len(june_2025_etfs)

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