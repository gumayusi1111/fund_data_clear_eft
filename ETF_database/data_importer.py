#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF数据导入脚本
将CSV文件中的ETF数据导入到PostgreSQL数据库
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# 导入数据库连接模块
from db_connection import ETFDatabaseManager

class ETFDataImporter:
    """ETF数据导入器"""
    
    def __init__(self):
        """初始化导入器"""
        self.db_manager = ETFDatabaseManager()
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """连接到数据库"""
        if self.db_manager.connect():
            self.connection = self.db_manager.connection
            self.cursor = self.db_manager.cursor
            return True
        return False
    
    def disconnect(self):
        """断开数据库连接"""
        self.db_manager.disconnect()
    
    def parse_csv_row(self, row):
        """解析CSV行数据"""
        try:
            # CSV格式: 代码,日期,开盘价,最高价,最低价,收盘价,上日收盘,涨跌,涨幅%,成交量(手数),成交额(千元)
            etf_code = row['代码'].strip()
            trade_date = datetime.strptime(row['日期'], '%Y%m%d').date()
            
            # 转换价格数据为Decimal类型（避免浮点数精度问题）
            open_price = Decimal(str(row['开盘价'])) if row['开盘价'] else None
            high_price = Decimal(str(row['最高价'])) if row['最高价'] else None
            low_price = Decimal(str(row['最低价'])) if row['最低价'] else None
            close_price = Decimal(str(row['收盘价'])) if row['收盘价'] else None
            
            # 新增字段：上日收盘、涨跌、涨幅%
            prev_close = Decimal(str(row['上日收盘'])) if row['上日收盘'] else None
            change_amount = Decimal(str(row['涨跌'])) if row['涨跌'] else None
            change_percent = Decimal(str(row['涨幅%'])) if row['涨幅%'] else None
            
            # 成交量和成交额（保持原始精度）
            volume = Decimal(str(row['成交量(手数)'])) if row['成交量(手数)'] else Decimal('0')
            amount = Decimal(str(row['成交额(千元)'])) if row['成交额(千元)'] else Decimal('0')
            
            return {
                'etf_code': etf_code,
                'trade_date': trade_date,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'prev_close': prev_close,
                'change_amount': change_amount,
                'change_percent': change_percent,
                'volume': volume,
                'amount': amount
            }
        except Exception as e:
            print(f"❌ 解析行数据失败: {e}")
            print(f"问题行数据: {row}")
            return None
    
    def import_csv_file(self, csv_file_path, table_name):
        """导入单个CSV文件到指定表"""
        if not os.path.exists(csv_file_path):
            print(f"❌ 文件不存在: {csv_file_path}")
            return False
        
        print(f"📂 开始导入: {csv_file_path}")
        
        try:
            # 读取CSV文件（处理UTF-8 BOM）
            with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
                csv_reader = csv.DictReader(f)
                
                insert_count = 0
                skip_count = 0
                
                for row in csv_reader:
                    # 解析行数据
                    parsed_data = self.parse_csv_row(row)
                    if not parsed_data:
                        skip_count += 1
                        continue
                    
                    # 插入数据库
                    if self.insert_record(parsed_data, table_name):
                        insert_count += 1
                    else:
                        skip_count += 1
                
                print(f"✅ 导入完成: {csv_file_path}")
                print(f"   📊 成功插入: {insert_count} 条记录")
                print(f"   ⚠️  跳过记录: {skip_count} 条记录")
                
                return True
                
        except Exception as e:
            print(f"❌ 导入失败: {csv_file_path}")
            print(f"   错误: {e}")
            return False
    
    def insert_record(self, data, table_name):
        """插入单条记录到数据库"""
        try:
            # 构建INSERT语句（使用ON CONFLICT处理重复数据）- 包含所有11个CSV字段
            insert_sql = f"""
                INSERT INTO {table_name} 
                (etf_code, trade_date, open_price, high_price, low_price, close_price, 
                 prev_close, change_amount, change_percent, volume, amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (etf_code, trade_date) 
                DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    prev_close = EXCLUDED.prev_close,
                    change_amount = EXCLUDED.change_amount,
                    change_percent = EXCLUDED.change_percent,
                    volume = EXCLUDED.volume,
                    amount = EXCLUDED.amount,
                    created_at = CURRENT_TIMESTAMP
            """
            
            self.cursor.execute(insert_sql, (
                data['etf_code'],
                data['trade_date'],
                data['open_price'],
                data['high_price'],
                data['low_price'],
                data['close_price'],
                data['prev_close'],
                data['change_amount'],
                data['change_percent'],
                data['volume'],
                data['amount']
            ))
            
            return True
            
        except Exception as e:
            print(f"❌ 插入记录失败: {e}")
            print(f"   数据: {data}")
            return False
    
    def import_etf_directory(self, etf_dir_path, table_name, limit=None):
        """导入ETF目录下的所有CSV文件"""
        if not os.path.exists(etf_dir_path):
            print(f"❌ 目录不存在: {etf_dir_path}")
            return False
        
        print(f"📁 开始导入目录: {etf_dir_path}")
        print(f"📊 目标表: {table_name}")
        
        # 获取所有CSV文件
        csv_files = list(Path(etf_dir_path).glob("*.csv"))
        
        if limit:
            csv_files = csv_files[:limit]
            print(f"🔍 测试模式：仅导入前 {limit} 个文件")
        
        print(f"📄 找到 {len(csv_files)} 个CSV文件")
        
        success_count = 0
        total_count = len(csv_files)
        
        try:
            for i, csv_file in enumerate(csv_files, 1):
                print(f"\n[{i}/{total_count}] 处理文件: {csv_file.name}")
                
                if self.import_csv_file(str(csv_file), table_name):
                    success_count += 1
                
                # 每10个文件提交一次事务
                if i % 10 == 0:
                    self.connection.commit()
                    print(f"💾 已提交前 {i} 个文件的数据")
            
            # 最终提交
            self.connection.commit()
            
            print(f"\n🎉 目录导入完成!")
            print(f"📊 总文件数: {total_count}")
            print(f"✅ 成功导入: {success_count}")
            print(f"❌ 失败文件: {total_count - success_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 目录导入失败: {e}")
            self.connection.rollback()
            return False
    
    def get_table_stats(self, table_name):
        """获取表的统计信息"""
        try:
            # 总记录数
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = self.cursor.fetchone()[0]
            
            # ETF数量
            self.cursor.execute(f"SELECT COUNT(DISTINCT etf_code) FROM {table_name}")
            etf_count = self.cursor.fetchone()[0]
            
            # 日期范围
            self.cursor.execute(f"SELECT MIN(trade_date), MAX(trade_date) FROM {table_name}")
            date_range = self.cursor.fetchone()
            
            print(f"\n📊 表 {table_name} 统计信息:")
            print(f"   总记录数: {total_records:,}")
            print(f"   ETF数量: {etf_count}")
            print(f"   日期范围: {date_range[0]} 到 {date_range[1]}")
            
            # 显示前几个ETF的记录数
            self.cursor.execute(f"""
                SELECT etf_code, COUNT(*) as record_count 
                FROM {table_name} 
                GROUP BY etf_code 
                ORDER BY record_count DESC 
                LIMIT 5
            """)
            
            top_etfs = self.cursor.fetchall()
            print(f"   记录数最多的ETF:")
            for etf_code, count in top_etfs:
                print(f"     {etf_code}: {count} 条记录")
            
            return True
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return False


def test_small_import():
    """测试小规模数据导入"""
    print("🧪 开始小规模测试导入...")
    
    importer = ETFDataImporter()
    
    if not importer.connect():
        print("❌ 数据库连接失败")
        return False
    
    try:
        # 测试导入前复权数据（仅前5个文件）
        etf_dir = "../ETF日更/0_ETF日K(前复权)"
        table_name = "basic_info_daily.forward_adjusted"
        
        result = importer.import_etf_directory(etf_dir, table_name, limit=5)
        
        if result:
            print("\n✅ 测试导入成功！")
            importer.get_table_stats(table_name)
        else:
            print("\n❌ 测试导入失败！")
        
        return result
        
    finally:
        importer.disconnect()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF数据导入工具')
    parser.add_argument('--mode', choices=['test', 'full'], default='test',
                        help='导入模式: test(测试5个文件), full(全部导入)')
    parser.add_argument('--table', choices=['forward', 'backward', 'ex_rights'], 
                        default='forward',
                        help='目标表: forward(前复权), backward(后复权), ex_rights(除权)')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制导入文件数量（仅用于测试）')
    
    args = parser.parse_args()
    
    # 表名映射（新的schema结构）
    table_mapping = {
        'forward': 'basic_info_daily.forward_adjusted',
        'backward': 'basic_info_daily.backward_adjusted', 
        'ex_rights': 'basic_info_daily.ex_rights'
    }
    
    # 目录映射
    dir_mapping = {
        'forward': '../ETF日更/0_ETF日K(前复权)',
        'backward': '../ETF日更/0_ETF日K(后复权)',
        'ex_rights': '../ETF日更/0_ETF日K(除权)'
    }
    
    table_name = table_mapping[args.table]
    etf_dir = dir_mapping[args.table]
    
    print(f"🚀 ETF数据导入工具")
    print(f"📊 模式: {args.mode}")
    print(f"📁 源目录: {etf_dir}")
    print(f"🎯 目标表: {table_name}")
    
    if args.mode == 'test':
        limit = args.limit or 5
        print(f"🔍 测试模式：导入前 {limit} 个文件")
    else:
        limit = args.limit
        print(f"📈 完整模式：导入所有文件")
    
    # 创建导入器
    importer = ETFDataImporter()
    
    if not importer.connect():
        print("❌ 数据库连接失败")
        return False
    
    try:
        # 执行导入
        result = importer.import_etf_directory(etf_dir, table_name, limit)
        
        if result:
            print("\n🎉 数据导入完成！")
            importer.get_table_stats(table_name)
        else:
            print("\n❌ 数据导入失败！")
        
        return result
        
    finally:
        importer.disconnect()


if __name__ == "__main__":
    main() 