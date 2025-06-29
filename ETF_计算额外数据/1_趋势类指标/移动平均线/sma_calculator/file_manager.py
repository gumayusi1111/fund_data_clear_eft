#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理器模块 - SMA专版
======================

专门负责SMA计算结果的文件管理和目录操作
支持智能目录创建、文件保存和路径管理
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional


class FileManager:
    """文件管理器 - SMA专版"""
    
    def __init__(self, output_dir: str):
        """
        初始化文件管理器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self.ensure_directory_exists(output_dir)
        print(f"📁 文件管理器初始化完成")
        print(f"   📂 输出目录: {output_dir}")
    
    def ensure_directory_exists(self, directory: str) -> bool:
        """
        确保目录存在，不存在则创建
        
        Args:
            directory: 目录路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"✅ 创建目录: {directory}")
            return True
        except Exception as e:
            print(f"❌ 创建目录失败: {directory}, 错误: {str(e)}")
            return False
    
    def create_output_directory(self, output_dir: Optional[str] = None) -> str:
        """
        创建输出目录 - 模仿WMA的实现
        
        Args:
            output_dir: 指定的输出目录，如果为None则使用默认
            
        Returns:
            str: 创建的目录路径
        """
        if output_dir is None:
            output_dir = self.output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 输出目录已创建: {output_dir}")
        return output_dir
    
    def save_json_result(self, data: Dict, filename: str, etf_code: str = "") -> bool:
        """
        保存JSON格式的结果
        
        Args:
            data: 要保存的数据
            filename: 文件名
            etf_code: ETF代码（用于子目录）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 如果有ETF代码，创建子目录
            if etf_code:
                save_dir = os.path.join(self.output_dir, etf_code)
                self.ensure_directory_exists(save_dir)
            else:
                save_dir = self.output_dir
            
            # 构建完整文件路径
            file_path = os.path.join(save_dir, filename)
            
            # 添加时间戳到数据中
            data_with_timestamp = data.copy()
            data_with_timestamp['_metadata'] = {
                'generated_time': datetime.now().isoformat(),
                'file_version': '1.0',
                'data_type': 'SMA_analysis'
            }
            
            # 保存JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_timestamp, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON文件已保存: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ JSON文件保存失败: {str(e)}")
            return False
    
    def save_csv_result(self, csv_content: str, filename: str, etf_code: str = "") -> bool:
        """
        保存CSV格式的结果
        
        Args:
            csv_content: CSV内容
            filename: 文件名
            etf_code: ETF代码（用于子目录）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 如果有ETF代码，创建子目录
            if etf_code:
                save_dir = os.path.join(self.output_dir, etf_code)
                self.ensure_directory_exists(save_dir)
            else:
                save_dir = self.output_dir
            
            # 构建完整文件路径
            file_path = os.path.join(save_dir, filename)
            
            # 保存CSV文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            print(f"✅ CSV文件已保存: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ CSV文件保存失败: {str(e)}")
            return False
    
    def get_output_file_path(self, filename: str, etf_code: str = "") -> str:
        """
        获取输出文件的完整路径
        
        Args:
            filename: 文件名
            etf_code: ETF代码（用于子目录）
            
        Returns:
            str: 完整文件路径
        """
        if etf_code:
            return os.path.join(self.output_dir, etf_code, filename)
        else:
            return os.path.join(self.output_dir, filename)
    
    def list_output_files(self, etf_code: str = "") -> List[str]:
        """
        列出输出目录中的文件
        
        Args:
            etf_code: ETF代码（指定子目录）
            
        Returns:
            List[str]: 文件列表
        """
        try:
            if etf_code:
                target_dir = os.path.join(self.output_dir, etf_code)
            else:
                target_dir = self.output_dir
            
            if not os.path.exists(target_dir):
                return []
            
            files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
            return sorted(files)
            
        except Exception as e:
            print(f"⚠️  列出文件失败: {str(e)}")
            return []
    
    def clean_old_files(self, days_to_keep: int = 7) -> bool:
        """
        清理指定天数前的旧文件
        
        Args:
            days_to_keep: 保留的天数
            
        Returns:
            bool: 是否清理成功
        """
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
            
            cleaned_count = 0
            
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                            print(f"🗑️  清理旧文件: {file}")
                        except Exception as e:
                            print(f"⚠️  清理文件失败: {file}, 错误: {str(e)}")
            
            if cleaned_count > 0:
                print(f"✅ 清理完成: 删除了 {cleaned_count} 个旧文件")
            else:
                print("✅ 无需清理: 没有超过保留期的文件")
            
            return True
            
        except Exception as e:
            print(f"❌ 清理旧文件失败: {str(e)}")
            return False
    
    def create_summary_report(self, results_summary: Dict) -> bool:
        """
        创建汇总报告
        
        Args:
            results_summary: 结果汇总数据
            
        Returns:
            bool: 是否创建成功
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"SMA_summary_report_{timestamp}.json"
            
            report_data = {
                'report_type': 'SMA_Summary',
                'generated_time': datetime.now().isoformat(),
                'summary': results_summary
            }
            
            return self.save_json_result(report_data, report_filename)
            
        except Exception as e:
            print(f"❌ 创建汇总报告失败: {str(e)}")
            return False
    
    def show_output_summary(self, output_dir: str):
        """
        显示输出摘要 - 模仿WMA的实现
        
        Args:
            output_dir: 输出目录
        """
        if not os.path.exists(output_dir):
            print("❌ 输出目录不存在")
            return
        
        try:
            files = []
            total_size = 0
            
            # 获取目录中的所有文件
            for root, dirs, filenames in os.walk(output_dir):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        files.append((file_path, file_size))
                        total_size += file_size
                    except:
                        pass
            
            print(f"\n📁 输出摘要 - {output_dir}")
            print("=" * 50)
            print(f"📊 文件总数: {len(files)}")
            print(f"💾 总大小: {self._format_file_size(total_size)}")
            
            if files:
                print(f"\n📄 文件列表:")
                for file_path, file_size in files:
                    file_name = os.path.basename(file_path)
                    print(f"   {file_name} ({self._format_file_size(file_size)})")
            
            print(f"\n💡 查看命令:")
            print(f"   cd {output_dir}")
            print(f"   ls -la")
            
        except Exception as e:
            print(f"❌ 显示输出摘要失败: {str(e)}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小显示
        
        Args:
            size_bytes: 字节数
            
        Returns:
            str: 格式化的大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB" 