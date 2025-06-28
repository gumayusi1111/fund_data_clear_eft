#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责加载和管理ETF初筛的各种配置参数
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """ETF初筛配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/filter_config.json
        """
        if config_path is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "config" / "filter_config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置文件加载成功: {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            raise
    
    def get_daily_data_source(self) -> Path:
        """获取日更数据源路径"""
        base_path = self.config_path.parent.parent
        source_path = base_path / self.config["paths"]["daily_data_source"] 
        return source_path.resolve()
    
    def get_output_base(self) -> Path:
        """获取输出基础路径"""
        base_path = self.config_path.parent.parent
        output_path = base_path / self.config["paths"]["output_base"]
        return output_path.resolve()
    
    def get_log_dir(self) -> Path:
        """获取日志目录路径"""
        base_path = self.config_path.parent.parent
        log_path = base_path / self.config["paths"]["log_dir"]
        return log_path.resolve()
    
    def get_复权类型(self) -> list:
        """获取复权类型列表"""
        return self.config["复权类型"]
    
    def get_筛选条件(self, category: str = None) -> Dict[str, Any]:
        """
        获取筛选条件
        
        Args:
            category: 条件类别，如 "基础条件"、"质量条件" 等
                     如果为None，返回所有条件
        """
        筛选条件 = self.config["筛选条件"]
        if category:
            return 筛选条件.get(category, {})
        return 筛选条件
    
    def get_输出设置(self) -> Dict[str, Any]:
        """获取输出设置"""
        return self.config["输出设置"]
    
    def get_日志设置(self) -> Dict[str, Any]:
        """获取日志设置"""
        return self.config["日志设置"]
    
    def get_筛选器权重(self) -> Dict[str, float]:
        """获取筛选器权重配置"""
        return self.config.get("筛选器权重", {
            "价格质量": 0.4,
            "流动性门槛": 0.6
        })
    
    def get_流动性门槛(self) -> Dict[str, Any]:
        """获取流动性门槛配置"""
        return self.config.get("流动性门槛", {})
    
    def get_价格质量标准(self) -> Dict[str, Any]:
        """获取价格质量标准配置"""
        return self.config.get("价格质量标准", {})
    
    def get_数据质量要求(self) -> Dict[str, Any]:
        """获取数据质量要求配置"""
        return self.config.get("数据质量要求", {})
    
    def get_异常波动阈值(self) -> Dict[str, Any]:
        """获取异常波动阈值配置"""
        return self.config.get("异常波动阈值", {})
    
    def get_筛选配置(self) -> Dict[str, Any]:
        """获取筛选配置"""
        return self.config.get("筛选配置", {})
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.get_output_base(),
            self.get_log_dir()
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def validate_config(self) -> bool:
        """验证配置有效性"""
        required_sections = ["paths", "复权类型", "流动性门槛", "价格质量标准", "输出设置"]
        
        for section in required_sections:
            if section not in self.config:
                print(f"❌ 配置缺少必要部分: {section}")
                return False
        
        # 验证日更数据源是否存在
        daily_source = self.get_daily_data_source()
        if not daily_source.exists():
            print(f"❌ 日更数据源不存在: {daily_source}")
            return False
            
        print("✅ 配置验证通过")
        return True
    
    def show_config_summary(self):
        """显示配置摘要"""
        print("\n" + "="*50)
        print("📋 ETF初筛配置摘要")
        print("="*50)
        print(f"日更数据源: {self.get_daily_data_source()}")
        print(f"输出目录: {self.get_output_base()}")
        print(f"日志目录: {self.get_log_dir()}")
        print(f"复权类型: {len(self.get_复权类型())}种")
        print(f"筛选条件: {len(self.get_筛选条件())}类")
        print("="*50)


# 全局配置实例
_global_config = None

def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config 