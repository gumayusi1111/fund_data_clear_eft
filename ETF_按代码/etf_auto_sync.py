#!/usr/bin/env python3
"""
ETF 数据自动同步脚本
1. 从百度网盘下载新增月份 RAR 文件
2. 解压并自动合并到本地历史目录
3. 清理临时文件
4. 自动管理文件哈希，避免重复下载
"""

import os
import sys
import shutil
import tempfile
import re
import subprocess
import json
import hashlib
from datetime import datetime
from typing import List, Tuple
from pathlib import Path

# 添加当前目录到 Python 路径以导入 etf_data_merger
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etf_data_merger import merge_two_folders

# 添加config目录到路径
config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
sys.path.insert(0, config_dir)

try:
    import sys
    import importlib.util
    hash_manager_path = os.path.join(config_dir, 'hash_manager.py')
    spec = importlib.util.spec_from_file_location("hash_manager", hash_manager_path)
    hash_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hash_manager_module)
    HashManager = hash_manager_module.HashManager
except ImportError:
    print("警告：无法导入哈希管理器，将跳过哈希验证功能")
    HashManager = None

try:
    from bypy import ByPy
except ImportError:
    print("错误：未安装 bypy，请运行: pip install bypy")
    sys.exit(1)


# 配置项
BAIDU_REMOTE_BASE = "/ETF"  # 百度网盘中 ETF 数据根目录
LOCAL_ETF_DIR = os.path.dirname(os.path.abspath(__file__))  # 本地 ETF_按代码 目录
CATEGORIES = ["0_ETF日K(前复权)", "0_ETF日K(后复权)", "0_ETF日K(除权)"]


def list_remote_files(bp: ByPy, remote_path: str) -> List[str]:
    """列出百度网盘指定路径下的文件列表"""
    try:
        # 使用 bypy 的 list 方法，它会输出到 stdout
        import io
        import sys
        from contextlib import redirect_stdout
        
        # 捕获 list 命令的输出
        f = io.StringIO()
        with redirect_stdout(f):
            bp.list(remote_path)
        
        output = f.getvalue()
        files = []
        
        # 解析输出，查找以 'F ' 开头的行（文件）
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('F '):
                # 格式: F 文件名 大小 日期时间 哈希
                parts = line.split(' ', 3)
                if len(parts) >= 2:
                    file_name = parts[1]
                    files.append(file_name)
        
        return files
    except Exception as e:
        print(f"列出远程文件失败: {e}")
        return []


def extract_rar(rar_path: str, extract_to: str) -> bool:
    """解压 RAR 文件"""
    try:
        # 检查是否安装了 unar (macOS) 或 unrar (Linux)
        unar_available = subprocess.run(['which', 'unar'], capture_output=True, text=True).returncode == 0
        unrar_available = subprocess.run(['which', 'unrar'], capture_output=True, text=True).returncode == 0
        
        if unar_available:
            # 使用 unar (macOS 推荐)
            cmd = ['unar', '-o', extract_to, rar_path]
        elif unrar_available:
            # 使用 unrar (Linux)
            cmd = ['unrar', 'x', '-o+', rar_path, extract_to]
        else:
            print("错误：未安装解压工具")
            print("macOS: brew install unar")
            print("Linux: apt install unrar")
            return False
        
        # 解压 RAR 文件
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 解压成功: {os.path.basename(rar_path)}")
            return True
        else:
            print(f"✗ 解压失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"解压出错: {e}")
        return False


def get_current_month_files(files: List[str]) -> List[Tuple[str, str, int, int]]:
    """
    查找当前月份的 RAR 文件
    返回: [(文件名, 类别, 年份, 月份), ...]
    """
    # 获取当前年月
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    print(f"当前时间: {current_year}年{current_month}月")
    
    pattern = r'(0_ETF日K\([^)]+\))_(\d{4})年(\d+)月\.rar$'
    current_month_files = []
    
    for file_name in files:
        match = re.match(pattern, file_name)
        if match:
            category = match.group(1)
            year = int(match.group(2))
            month = int(match.group(3))
            
            # 只处理当前月份的文件
            if year == current_year and month == current_month:
                current_month_files.append((file_name, category, year, month))
    
    return current_month_files


def sync_current_month_data():
    """同步当前月份的数据"""
    print("开始同步当前月份的 ETF 数据...")
    
    # 初始化哈希管理器
    hash_manager = None
    if HashManager:
        try:
            hash_manager = HashManager()
            print("✓ 哈希管理器初始化成功")
            hash_manager.print_status()
            
            # 清理旧的哈希记录
            hash_manager.clean_old_hashes()
        except Exception as e:
            print(f"⚠️ 哈希管理器初始化失败: {e}")
            hash_manager = None
    
    # 初始化 bypy
    bp = ByPy()
    
    # 获取远程文件列表
    print("获取百度网盘文件列表...")
    remote_files = list_remote_files(bp, BAIDU_REMOTE_BASE)
    if not remote_files:
        print("未找到任何文件")
        return
    
    # 查找当前月份文件
    current_month_files = get_current_month_files(remote_files)
    if not current_month_files:
        now = datetime.now()
        print(f"未找到 {now.year}年{now.month}月 的 RAR 文件")
        print("可能原因：")
        print("1. 当月数据尚未上传到百度网盘")
        print("2. 文件命名格式不匹配")
        return
    
    print(f"找到当前月份的 {len(current_month_files)} 个文件:")
    for file_name, category, year, month in current_month_files:
        print(f"  - {file_name}")
    
    # 检查哈希，过滤已下载的文件
    files_to_download = []
    if hash_manager:
        print("\n🔍 检查文件哈希...")
        for file_name, category, year, month in current_month_files:
            if hash_manager.is_file_downloaded(file_name):
                print(f"⏭️ 跳过已下载的文件: {file_name}")
            else:
                files_to_download.append((file_name, category, year, month))
                print(f"📥 需要下载: {file_name}")
    else:
        files_to_download = current_month_files
    
    if not files_to_download:
        print("🎉 所有文件都已是最新，无需下载！")
        return
    
    # 检查是否有完整的三个类别
    found_categories = set(category for _, category, _, _ in files_to_download)
    expected_categories = set(CATEGORIES)
    missing_categories = expected_categories - found_categories
    
    if missing_categories:
        print(f"⚠️ 缺少以下类别的文件: {', '.join(missing_categories)}")
        print("将只处理已找到的文件...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="etf_sync_current_")
    print(f"临时目录: {temp_dir}")
    
    try:
        success_count = 0
        # 下载并处理每个文件
        for file_name, category, year, month in files_to_download:
            print(f"\n处理 {file_name}...")
            
            # 下载文件
            remote_file_path = f"{BAIDU_REMOTE_BASE}/{file_name}"
            local_rar_path = os.path.join(temp_dir, file_name)
            
            print(f"下载中...")
            try:
                bp.downfile(remote_file_path, local_rar_path)
                print(f"✓ 下载完成")
                
                # 更新哈希
                if hash_manager:
                    hash_manager.update_file_hash(file_name, local_rar_path)
                    
            except Exception as e:
                print(f"✗ 下载失败: {e}")
                continue
            
            # 解压文件
            extract_dir = os.path.join(temp_dir, f"extract_{category}_{year}_{month}")
            os.makedirs(extract_dir, exist_ok=True)
            
            if not extract_rar(local_rar_path, extract_dir):
                continue
            
            # 查找解压后的目录
            extracted_dirs = [d for d in os.listdir(extract_dir) 
                            if os.path.isdir(os.path.join(extract_dir, d)) and category in d]
            
            if not extracted_dirs:
                print(f"✗ 未找到解压后的目录")
                continue
            
            extracted_data_dir = os.path.join(extract_dir, extracted_dirs[0])
            
            # 合并到对应的历史目录
            hist_dir = os.path.join(LOCAL_ETF_DIR, category)
            if os.path.isdir(hist_dir):
                print(f"合并到 {category}...")
                merge_two_folders(hist_dir, extracted_data_dir)
                print(f"✓ 合并完成")
                success_count += 1
            else:
                print(f"✗ 历史目录不存在: {hist_dir}")
        
        # 汇总结果
        now = datetime.now()
        print(f"\n🎉 {now.year}年{now.month}月数据同步完成!")
        print(f"成功处理: {success_count}/{len(files_to_download)} 个文件")
        
        if success_count > 0:
            print(f"数据已更新到: {LOCAL_ETF_DIR}")
            
        # 显示哈希管理器最终状态
        if hash_manager:
            print("\n📊 哈希管理器最终状态:")
            hash_manager.print_status()
        
    finally:
        # 清理临时目录
        print(f"清理临时目录...")
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_connection():
    """测试百度网盘连接和列出文件"""
    print("测试百度网盘连接...")
    bp = ByPy()
    
    # 测试基本连接
    try:
        bp.info()
        print("✓ 连接成功")
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False
    
    # 测试列出 ETF 目录
    print(f"\n测试列出 {BAIDU_REMOTE_BASE} 目录...")
    try:
        files = list_remote_files(bp, BAIDU_REMOTE_BASE)
        if files:
            print(f"✓ 找到 {len(files)} 个文件:")
            for file_name in files[:10]:  # 显示前10个
                print(f"  - {file_name}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
                
            # 查找当前月份文件
            current_files = get_current_month_files(files)
            if current_files:
                print(f"\n找到当前月份的 {len(current_files)} 个文件:")
                for file_name, category, year, month in current_files:
                    print(f"  - {file_name} ({category})")
                    
                # 测试哈希管理
                if HashManager:
                    hash_manager = HashManager()
                    print(f"\n📊 哈希管理器状态:")
                    hash_manager.print_status()
            else:
                now = datetime.now()
                print(f"\n未找到 {now.year}年{now.month}月 的文件")
        else:
            print("✗ 未找到任何文件")
    except Exception as e:
        print(f"✗ 列出文件失败: {e}")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_connection()
    else:
        sync_current_month_data() 