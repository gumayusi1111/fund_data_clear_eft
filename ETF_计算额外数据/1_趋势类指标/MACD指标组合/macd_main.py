#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD指标组合系统 - 主程序
========================

专业的MACD技术指标计算系统
🎯 功能: DIF+DEA+MACD三线组合分析、金叉死叉识别、零轴分析
📊 输出: 完整的MACD指标数据和交易信号分析
⚙️ 参数: 支持标准(12,26,9)、敏感(8,17,9)、平滑(19,39,9)配置

"""

import sys
import os
from datetime import datetime

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from macd_calculator.controller import MACDController


def print_welcome_banner():
    """打印欢迎信息"""
    print("=" * 70)
    print(" " * 15 + "MACD指标组合计算系统")
    print("=" * 70)
    print("🎯 Moving Average Convergence Divergence Analysis")
    print("📊 专业技术指标: DIF + DEA + MACD + 信号分析")
    print("⚙️ 三种参数配置: 标准(12,26,9) | 敏感(8,17,9) | 平滑(19,39,9)")
    print("🎲 信号识别: 金叉死叉 | 零轴穿越 | 背离分析")
    print("=" * 70)
    print()


def print_menu():
    """打印菜单选项"""
    print("📋 功能菜单:")
    print("1️⃣  处理3000万门槛ETF (标准参数)")
    print("2️⃣  处理5000万门槛ETF (标准参数)")
    print("3️⃣  处理3000万门槛ETF (敏感参数)")
    print("4️⃣  处理5000万门槛ETF (敏感参数)")
    print("5️⃣  处理3000万门槛ETF (平滑参数)")
    print("6️⃣  处理5000万门槛ETF (平滑参数)")
    print("7️⃣  测试单个ETF")
    print("8️⃣  系统状态检查")
    print("9️⃣  退出程序")
    print("-" * 50)


def main():
    """主程序入口"""
    print_welcome_banner()
    
    while True:
        print_menu()
        choice = input("请选择功能 (1-9): ").strip()
        
        try:
            if choice == '1':
                # 3000万门槛 - 标准参数
                print("🚀 开始处理3000万门槛ETF (标准参数)...")
                controller = MACDController('standard')
                result = controller.process_by_threshold("3000万门槛")
                
            elif choice == '2':
                # 5000万门槛 - 标准参数
                print("🚀 开始处理5000万门槛ETF (标准参数)...")
                controller = MACDController('standard')
                result = controller.process_by_threshold("5000万门槛")
                
            elif choice == '3':
                # 3000万门槛 - 敏感参数
                print("🚀 开始处理3000万门槛ETF (敏感参数)...")
                controller = MACDController('sensitive')
                result = controller.process_by_threshold("3000万门槛")
                
            elif choice == '4':
                # 5000万门槛 - 敏感参数
                print("🚀 开始处理5000万门槛ETF (敏感参数)...")
                controller = MACDController('sensitive')
                result = controller.process_by_threshold("5000万门槛")
                
            elif choice == '5':
                # 3000万门槛 - 平滑参数
                print("🚀 开始处理3000万门槛ETF (平滑参数)...")
                controller = MACDController('smooth')
                result = controller.process_by_threshold("3000万门槛")
                
            elif choice == '6':
                # 5000万门槛 - 平滑参数
                print("🚀 开始处理5000万门槛ETF (平滑参数)...")
                controller = MACDController('smooth')
                result = controller.process_by_threshold("5000万门槛")
                
            elif choice == '7':
                # 测试单个ETF
                controller = MACDController('standard')
                
                etf_code = input("请输入ETF代码 (默认159696): ").strip()
                if not etf_code:
                    etf_code = "159696"
                
                print(f"🧪 开始测试ETF: {etf_code}")
                test_result = controller.test_single_etf(etf_code)
                
                print("\n📊 测试结果:")
                for step, details in test_result['steps'].items():
                    print(f"  {step}: {details}")
                
            elif choice == '8':
                # 系统状态检查
                controller = MACDController('standard')
                status = controller.get_system_status()
                
                print("\n📊 系统状态信息:")
                print(f"  系统名称: {status['system_name']}")
                print(f"  版本号: {status['version']}")
                print(f"  启动时间: {status['start_time']}")
                print(f"  运行时长: {status['runtime_seconds']:.2f} 秒")
                print(f"  数据源: {status['data_source']}")
                print(f"  输出目录: {status['output_directory']}")
                
            elif choice == '9':
                # 退出程序
                print("👋 感谢使用MACD指标计算系统，再见！")
                break
                
            else:
                print("❌ 无效选择，请输入1-9之间的数字")
                continue
                
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断程序执行")
            break
            
        except Exception as e:
            print(f"❌ 程序执行出错: {e}")
            print("请检查系统状态或联系技术支持")
        
        # 询问是否继续
        print("\n" + "=" * 50)
        continue_choice = input("是否继续使用? (y/n): ").strip().lower()
        if continue_choice in ['n', 'no', '否']:
            print("👋 感谢使用MACD指标计算系统，再见！")
            break
        print()


def quick_test():
    """快速测试模式"""
    print("🧪 MACD系统快速测试模式")
    print("=" * 50)
    
    try:
        # 初始化控制器
        controller = MACDController('standard')
        
        # 测试ETF
        test_etf = "159696"
        print(f"📊 测试ETF: {test_etf}")
        
        test_result = controller.test_single_etf(test_etf)
        
        print("✅ 测试完成")
        print(f"📊 测试结果: {test_result}")
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")


if __name__ == "__main__":
    # 检查是否是快速测试模式
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        quick_test()
    else:
        main() 