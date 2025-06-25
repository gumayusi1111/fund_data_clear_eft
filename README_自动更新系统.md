# ETF数据自动更新系统

## 🎯 系统概述

这是一个全自动的ETF数据更新系统，可以每日自动从百度网盘下载最新的ETF数据，解压并合并到本地数据库中。

### 核心功能
- ✅ **自动下载**：每日从百度网盘下载当前月份的ETF数据
- ✅ **智能检测**：通过文件哈希值检测数据是否有更新
- ✅ **增量合并**：只更新有变化的数据，保持历史数据完整
- ✅ **定时执行**：支持定时任务，无需人工干预
- ✅ **错误处理**：完善的错误处理和日志记录
- ✅ **通知系统**：可选的钉钉/企业微信通知

## 🚀 快速开始

### 1. 安装和配置

```bash
# 运行安装配置向导
python setup_auto_updater.py
```

安装向导会自动：
- 安装必要的Python依赖包
- 检查并提示安装unar解压工具
- 配置百度网盘授权
- 创建启动脚本
- 可选设置系统服务

### 2. 百度网盘授权

第一次使用需要授权bypy访问你的百度网盘：

```bash
bypy info
```

按照提示完成授权（需要百度账号登录）。

### 3. 运行更新

```bash
# 手动运行一次更新
python etf_auto_updater.py once

# 启动定时更新服务
python etf_auto_updater.py schedule
```

## 📋 系统要求

### 必需依赖
- Python 3.7+
- pandas (数据处理)
- requests (网络请求)
- schedule (定时任务)
- bypy (百度网盘命令行工具)
- unar (解压RAR文件)

### 支持平台
- ✅ macOS (推荐使用Homebrew安装unar)
- ✅ Linux (Ubuntu/CentOS等，使用包管理器安装unar)
- ⚠️ Windows (需要手动安装unar)

## ⚙️ 配置说明

配置文件：`config.json`

```json
{
    "baidu_netdisk": {
        "share_url": "https://pan.baidu.com/s/1aZlvjI8dh3Cqs3nyMuYxlA",
        "password": "3gln",
        "download_method": "bypy"
    },
    "update_schedule": {
        "time": "09:00",        // 更新时间
        "enabled": true         // 是否启用定时更新
    },
    "notification": {
        "enabled": false,       // 是否启用通知
        "webhook_url": ""       // 钉钉/企业微信Webhook URL
    },
    "base_dir": ".",           // 工作目录
    "log_level": "INFO"        // 日志级别
}
```

## 🔄 工作流程

```
1. 检查当前月份 → "2024年06月"
   ↓
2. 构造文件名 → ["0_ETF日K(前复权)_2024年06月.rar", ...]
   ↓
3. 下载文件 → temp/目录
   ↓
4. 检查文件哈希 → 是否有变化？
   ↓
5. 解压RAR文件 → temp/extracted/
   ↓
6. 合并数据 → ETF/merged_data/
   ↓
7. 清理临时文件 → 完成
```

## 📁 目录结构

```
data_clear/
├── ETF/
│   └── merged_data/
│       ├── 前复权/     (1185+ CSV文件)
│       ├── 后复权/     (1185+ CSV文件)
│       └── 除权/       (1185+ CSV文件)
├── temp/               (临时文件，自动清理)
├── etf_auto_updater.py (主程序)
├── setup_auto_updater.py (安装向导)
├── config.json         (配置文件)
├── file_hashes.json    (文件哈希记录)
├── etf_updater.log     (日志文件)
└── start_etf_updater.sh (启动脚本)
```

## 🛠️ 高级用法

### 作为系统服务运行

#### macOS (launchd)
```bash
# 安装服务
launchctl load ~/Library/LaunchAgents/com.etf.autoupdater.plist
launchctl start com.etf.autoupdater

# 停止服务
launchctl stop com.etf.autoupdater
launchctl unload ~/Library/LaunchAgents/com.etf.autoupdater.plist
```

#### Linux (systemd)
```bash
# 创建服务文件
sudo cp etf-updater.service /etc/systemd/system/
sudo systemctl enable etf-updater.service
sudo systemctl start etf-updater.service

# 查看状态
sudo systemctl status etf-updater.service
```

### 通知配置

支持钉钉群机器人通知：

1. 在钉钉群中添加机器人
2. 获取Webhook URL
3. 更新config.json中的notification配置

## 🐛 故障排除

### 常见问题

1. **bypy授权失败**
   ```bash
   # 重新授权
   bypy info
   ```

2. **unar未安装**
   ```bash
   # macOS
   brew install unar
   
   # Ubuntu/Debian
   sudo apt-get install unar
   
   # CentOS/RHEL
   sudo yum install unar
   ```

3. **权限问题**
   ```bash
   # 确保脚本有执行权限
   chmod +x start_etf_updater.sh
   ```

4. **Python依赖问题**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

### 查看日志

```bash
# 实时查看日志
tail -f etf_updater.log

# 查看最近的错误
grep ERROR etf_updater.log
```

## 🔧 自定义开发

系统采用模块化设计，可以轻松扩展：

```python
# 自定义通知方式
def custom_notification(message):
    # 实现你的通知逻辑
    pass

# 自定义数据处理
def custom_data_processor(data):
    # 实现你的数据处理逻辑
    return processed_data
```

## 📈 性能优化

- 使用文件哈希值避免重复下载
- 增量数据合并，只更新变化的文件
- 自动清理临时文件，节省磁盘空间
- 多线程下载（可选扩展）

## ⚠️ 注意事项

1. **网络环境**：确保网络稳定，百度网盘访问正常
2. **磁盘空间**：预留足够空间存储数据（建议2GB+）
3. **百度网盘限制**：注意下载频率，避免触发限制
4. **数据备份**：建议定期备份重要数据

## 🤝 技术支持

如果遇到问题，请检查：
1. 日志文件 `etf_updater.log`
2. 配置文件 `config.json`
3. 网络连接和百度网盘授权状态

## 📄 许可证

本项目为个人使用，请遵守相关数据提供方的使用条款。 