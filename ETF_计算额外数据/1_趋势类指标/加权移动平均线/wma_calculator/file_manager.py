#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMA文件管理器模块
================

专门负责输出目录管理和文件操作
"""

import os
import shutil
from datetime import datetime
from typing import Optional, List


class FileManager:
    """WMA文件管理器"""
    
    def __init__(self, base_output_dir: str = "data"):
        """
        初始化文件管理器
        
        Args:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = base_output_dir
        self.current_session_dir = None
        print("📁 文件管理器初始化完成")
    
    def create_output_directory(self, output_dir: Optional[str] = None) -> str:
        """
        创建输出目录
        
        Args:
            output_dir: 指定的输出目录，如果为None则使用默认
            
        Returns:
            str: 创建的目录路径
        """
        if output_dir is None:
            output_dir = self.base_output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 输出目录已创建: {output_dir}")
        return output_dir
    
    def create_session_directory(self, session_prefix: str = "WMA_Session") -> str:
        """
        创建会话目录（带时间戳）
        
        Args:
            session_prefix: 会话目录前缀
            
        Returns:
            str: 会话目录路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_dir = os.path.join(self.base_output_dir, f"{session_prefix}_{timestamp}")
        
        os.makedirs(session_dir, exist_ok=True)
        self.current_session_dir = session_dir
        
        print(f"📁 会话目录已创建: {session_dir}")
        return session_dir
    
    def cleanup_old_sessions(self, keep_count: int = 5):
        """
        清理旧的会话目录，只保留最新的几个
        
        Args:
            keep_count: 保留的会话数量
        """
        if not os.path.exists(self.base_output_dir):
            return
        
        try:
            # 获取所有会话目录
            session_dirs = []
            for item in os.listdir(self.base_output_dir):
                item_path = os.path.join(self.base_output_dir, item)
                if os.path.isdir(item_path) and item.startswith('WMA_Session_'):
                    session_dirs.append((item_path, os.path.getctime(item_path)))
            
            # 按创建时间排序
            session_dirs.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出保留数量的目录
            if len(session_dirs) > keep_count:
                for session_path, _ in session_dirs[keep_count:]:
                    shutil.rmtree(session_path)
                    print(f"🗑️  已清理旧会话: {os.path.basename(session_path)}")
                
                print(f"✅ 会话清理完成，保留最新 {keep_count} 个")
            
        except Exception as e:
            print(f"❌ 会话清理失败: {e}")
    
    def get_output_files(self, directory: str) -> List[str]:
        """
        获取目录中的输出文件列表
        
        Args:
            directory: 目录路径
            
        Returns:
            List[str]: 文件路径列表
        """
        if not os.path.exists(directory):
            return []
        
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                files.append(item_path)
        
        return sorted(files)
    
    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小（字节）
        """
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def calculate_directory_size(self, directory: str) -> int:
        """
        计算目录大小
        
        Args:
            directory: 目录路径
            
        Returns:
            int: 目录大小（字节）
        """
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        except:
            pass
        
        return total_size
    
    def format_file_size(self, size_bytes: int) -> str:
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
    
    def show_output_summary(self, output_dir: str):
        """
        显示输出摘要
        
        Args:
            output_dir: 输出目录
        """
        if not os.path.exists(output_dir):
            print("❌ 输出目录不存在")
            return
        
        files = self.get_output_files(output_dir)
        total_size = self.calculate_directory_size(output_dir)
        
        print(f"\n📁 输出摘要 - {output_dir}")
        print("=" * 50)
        print(f"📊 文件总数: {len(files)}")
        print(f"💾 总大小: {self.format_file_size(total_size)}")
        
        if files:
            print(f"\n📄 文件列表:")
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_size = self.get_file_size(file_path)
                print(f"   {file_name} ({self.format_file_size(file_size)})")
        
        print(f"\n💡 查看命令:")
        print(f"   cd {output_dir}")
        print(f"   ls -la") 