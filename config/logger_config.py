#!/usr/bin/env python3
"""
日志配置模块
为ETF数据同步系统提供统一的日志配置
"""

import os
import json
import logging
import logging.handlers
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"警告：无法加载配置文件 {config_path}: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "logging": {
            "level": "INFO",
            "file_path": "./logs/etf_sync.log",
            "max_size_mb": 10,
            "backup_count": 5,
            "console_output": True,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


def setup_logger(name: str = "etf_sync") -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    config = load_config()
    log_config = config.get("logging", {})
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_config.get("level", "INFO")))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    
    # 文件处理器
    log_file_path = log_config.get("file_path", "./logs/etf_sync.log")
    log_dir = os.path.dirname(log_file_path)
    
    # 确保日志目录存在
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 使用RotatingFileHandler实现日志轮转
    max_size = log_config.get("max_size_mb", 10) * 1024 * 1024  # 转换为字节
    backup_count = log_config.get("backup_count", 5)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    if log_config.get("console_output", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def log_system_info(logger: logging.Logger):
    """记录系统信息"""
    import platform
    import sys
    from datetime import datetime
    
    logger.info("=" * 50)
    logger.info("ETF数据同步系统启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info("=" * 50)


if __name__ == "__main__":
    # 测试日志配置
    test_logger = setup_logger("test")
    log_system_info(test_logger)
    test_logger.info("这是一条测试日志信息")
    test_logger.warning("这是一条警告信息")
    test_logger.error("这是一条错误信息")
    print("日志测试完成，请检查logs目录中的日志文件") 