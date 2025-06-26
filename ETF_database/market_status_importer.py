#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF市场状况JSON数据导入程序
处理etf_market_status.json文件并导入到PostgreSQL数据库
"""

import json
import os
from datetime import datetime
from db_connection import ETFDatabaseManager
from typing import Dict, Any, Optional

class MarketStatusImporter:
    """ETF市场状况数据导入器"""
    
    def __init__(self):
        self.db_manager = ETFDatabaseManager()
        
    def connect(self):
        """连接数据库"""
        return self.db_manager.connect()
    
    def disconnect(self):
        """断开数据库连接"""
        self.db_manager.disconnect()
    
    @property
    def cursor(self):
        """获取数据库游标"""
        return self.db_manager.cursor
    
    def create_market_status_tables(self):
        """创建市场状况相关表"""
        
        # 创建schema
        self.cursor.execute("CREATE SCHEMA IF NOT EXISTS basic_info_market")
        
        # 创建ETF状况表
        create_etf_status_sql = """
        CREATE TABLE IF NOT EXISTS basic_info_market.etf_status (
            id SERIAL PRIMARY KEY,
            etf_code VARCHAR(20) NOT NULL,
            status VARCHAR(50) NOT NULL,
            status_code VARCHAR(20) NOT NULL,
            latest_date DATE,
            days_behind INTEGER DEFAULT 0,
            analysis TEXT,
            last_check TIMESTAMP,
            check_time_info TEXT,
            report_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(etf_code, report_date)
        )
        """
        
        # 创建报告信息表
        create_report_info_sql = """
        CREATE TABLE IF NOT EXISTS basic_info_market.report_info (
            id SERIAL PRIMARY KEY,
            generated_time TIMESTAMP NOT NULL,
            total_etf_count INTEGER NOT NULL,
            data_source VARCHAR(100),
            latest_trading_day DATE,
            active_count INTEGER DEFAULT 0,
            normal_count INTEGER DEFAULT 0,
            suspended_count INTEGER DEFAULT 0,
            delisted_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            report_date DATE NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            print("🔧 创建市场状况数据表...")
            self.cursor.execute(create_etf_status_sql)
            self.cursor.execute(create_report_info_sql)
            self.db_manager.connection.commit()
            print("✅ 数据表创建成功!")
            return True
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def parse_json_file(self, json_file_path: str) -> Optional[Dict[str, Any]]:
        """解析JSON文件"""
        try:
            print(f"📖 读取JSON文件: {json_file_path}")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON文件解析成功")
            print(f"📊 报告生成时间: {data['report_info']['generated_time']}")
            print(f"📈 ETF总数: {data['report_info']['total_etf_count']}")
            print(f"🔍 活跃ETF: {data['status_summary']['active_count']}")
            print(f"⚠️  可能退市: {data['status_summary']['delisted_count']}")
            
            return data
        except Exception as e:
            print(f"❌ JSON文件解析失败: {e}")
            return None
    
    def import_report_info(self, report_data: Dict[str, Any]) -> bool:
        """导入报告信息"""
        try:
            report_info = report_data['report_info']
            status_summary = report_data['status_summary']
            
            # 解析时间
            generated_time = datetime.strptime(
                report_info['generated_time'], 
                '%Y-%m-%d %H:%M:%S'
            )
            latest_trading_day = datetime.strptime(
                report_info['latest_trading_day'], 
                '%Y-%m-%d'
            ).date()
            
            report_date = generated_time.date()
            
            insert_sql = """
            INSERT INTO basic_info_market.report_info 
            (generated_time, total_etf_count, data_source, latest_trading_day,
             active_count, normal_count, suspended_count, delisted_count, error_count, report_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (report_date) DO UPDATE SET
                generated_time = EXCLUDED.generated_time,
                total_etf_count = EXCLUDED.total_etf_count,
                data_source = EXCLUDED.data_source,
                latest_trading_day = EXCLUDED.latest_trading_day,
                active_count = EXCLUDED.active_count,
                normal_count = EXCLUDED.normal_count,
                suspended_count = EXCLUDED.suspended_count,
                delisted_count = EXCLUDED.delisted_count,
                error_count = EXCLUDED.error_count
            """
            
            self.cursor.execute(insert_sql, (
                generated_time,
                report_info['total_etf_count'],
                report_info['data_source'],
                latest_trading_day,
                status_summary['active_count'],
                status_summary['normal_count'],
                status_summary['suspended_count'],
                status_summary['delisted_count'],
                status_summary['error_count'],
                report_date
            ))
            
            print("✅ 报告信息导入成功")
            return True
            
        except Exception as e:
            print(f"❌ 报告信息导入失败: {e}")
            return False
    
    def import_etf_status(self, report_data: Dict[str, Any]) -> bool:
        """导入ETF状况数据"""
        try:
            etf_details = report_data['etf_details']
            report_date = datetime.strptime(
                report_data['report_info']['generated_time'], 
                '%Y-%m-%d %H:%M:%S'
            ).date()
            
            insert_sql = """
            INSERT INTO basic_info_market.etf_status 
            (etf_code, status, status_code, latest_date, days_behind, 
             analysis, last_check, check_time_info, report_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (etf_code, report_date) DO UPDATE SET
                status = EXCLUDED.status,
                status_code = EXCLUDED.status_code,
                latest_date = EXCLUDED.latest_date,
                days_behind = EXCLUDED.days_behind,
                analysis = EXCLUDED.analysis,
                last_check = EXCLUDED.last_check,
                check_time_info = EXCLUDED.check_time_info
            """
            
            success_count = 0
            total_count = len(etf_details)
            
            print(f"📊 开始导入{total_count}个ETF状况记录...")
            
            for etf_code, etf_info in etf_details.items():
                try:
                    # 解析日期
                    latest_date = datetime.strptime(
                        etf_info['latest_date'], 
                        '%Y-%m-%d'
                    ).date()
                    
                    last_check = datetime.strptime(
                        etf_info['last_check'], 
                        '%Y-%m-%d %H:%M:%S'
                    )
                    
                    self.cursor.execute(insert_sql, (
                        etf_info['code'],
                        etf_info['status'],
                        etf_info['status_code'],
                        latest_date,
                        etf_info['days_behind'],
                        etf_info['analysis'],
                        last_check,
                        etf_info['check_time_info'],
                        report_date
                    ))
                    
                    success_count += 1
                    
                    # 每100条记录显示进度
                    if success_count % 100 == 0:
                        print(f"  📈 已处理: {success_count}/{total_count}")
                        
                except Exception as e:
                    print(f"⚠️  ETF {etf_code} 导入失败: {e}")
            
            print(f"✅ ETF状况导入完成: {success_count}/{total_count}")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ ETF状况导入失败: {e}")
            return False
    
    def import_market_status_json(self, json_file_path: str) -> bool:
        """导入完整的市场状况JSON文件"""
        
        if not os.path.exists(json_file_path):
            print(f"❌ 文件不存在: {json_file_path}")
            return False
        
        # 解析JSON文件
        report_data = self.parse_json_file(json_file_path)
        if not report_data:
            return False
        
        try:
            # 创建表（如果不存在）
            if not self.create_market_status_tables():
                return False
            
            # 导入报告信息
            if not self.import_report_info(report_data):
                return False
            
            # 导入ETF状况
            if not self.import_etf_status(report_data):
                return False
            
            # 提交事务
            self.db_manager.connection.commit()
            print("🎉 市场状况数据导入完成!")
            return True
            
        except Exception as e:
            print(f"❌ 导入过程失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def show_import_summary(self):
        """显示导入汇总信息"""
        try:
            # 报告信息统计
            self.cursor.execute("SELECT COUNT(*) FROM basic_info_market.report_info")
            report_count = self.cursor.fetchone()[0]
            
            # ETF状况统计
            self.cursor.execute("SELECT COUNT(*) FROM basic_info_market.etf_status")
            status_count = self.cursor.fetchone()[0]
            
            # 最新报告日期
            self.cursor.execute("""
                SELECT report_date, total_etf_count, active_count, delisted_count 
                FROM basic_info_market.report_info 
                ORDER BY report_date DESC LIMIT 1
            """)
            latest_report = self.cursor.fetchone()
            
            # 状态分布
            self.cursor.execute("""
                SELECT status, COUNT(*) 
                FROM basic_info_market.etf_status 
                WHERE report_date = (SELECT MAX(report_date) FROM basic_info_market.etf_status)
                GROUP BY status 
                ORDER BY COUNT(*) DESC
            """)
            status_distribution = self.cursor.fetchall()
            
            print("\n📊 导入汇总信息:")
            print(f"  📈 报告数量: {report_count}")
            print(f"  📊 ETF状况记录: {status_count}")
            
            if latest_report:
                print(f"  📅 最新报告: {latest_report[0]}")
                print(f"  🎯 ETF总数: {latest_report[1]}")
                print(f"  ✅ 活跃ETF: {latest_report[2]}")
                print(f"  ⚠️  可能退市: {latest_report[3]}")
            
            if status_distribution:
                print(f"  📈 状态分布:")
                for status, count in status_distribution:
                    print(f"    {status}: {count}")
                    
        except Exception as e:
            print(f"❌ 汇总信息获取失败: {e}")


def main():
    """主函数"""
    print("🚀 ETF市场状况JSON数据导入程序")
    
    # JSON文件路径
    json_file_path = "../ETF市场状况/etf_market_status.json"
    
    # 创建导入器
    importer = MarketStatusImporter()
    
    try:
        # 连接数据库
        if not importer.connect():
            print("❌ 数据库连接失败")
            return False
        
        # 导入数据
        success = importer.import_market_status_json(json_file_path)
        
        if success:
            # 显示汇总信息
            importer.show_import_summary()
        
        return success
        
    finally:
        # 断开数据库连接
        importer.disconnect()


if __name__ == "__main__":
    main() 