#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF数据处理器
负责协调整个筛选流程，管理筛选器链，处理筛选结果
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..data_loader import ETFDataLoader
from ..filters import VolumeFilter, QualityFilter, FilterResult
from ..utils.config import get_config
from ..utils.logger import get_logger, ProcessTimer


class ETFDataProcessor:
    """ETF数据处理器主类"""
    
    def __init__(self, threshold_name: str = "5000万门槛"):
        self.config = get_config()
        self.logger = get_logger()
        self.data_loader = ETFDataLoader()
        self.threshold_name = threshold_name
        
        # 初始化筛选器
        self._init_filters()
        
    def _init_filters(self):
        """初始化筛选器链"""
        # 构建新的配置结构
        筛选配置 = {
            "流动性门槛": self.config.get_流动性门槛(),
            "价格质量标准": self.config.get_价格质量标准(),
            "数据质量要求": self.config.get_数据质量要求(),
            "异常波动阈值": self.config.get_异常波动阈值(),
            "筛选配置": self.config.get_筛选配置()
        }
        
        self.filters = {
            "价格质量": QualityFilter(筛选配置),
            "流动性门槛": VolumeFilter(筛选配置, self.threshold_name)
        }
        
        self.logger.info(f"✅ 初始化 {len(self.filters)} 个筛选器")
    
    def process_all_etfs(self, 复权类型: str = "0_ETF日K(前复权)", 
                        days_back: int = None) -> Dict[str, Any]:
        """
        处理所有ETF数据的完整筛选流程
        
        Args:
            复权类型: 复权类型
            days_back: 加载最近N天的数据
        
        Returns:
            完整的处理结果
        """
        with ProcessTimer("ETF初筛处理", self.logger):
            # 1. 加载数据
            etf_codes = self.data_loader.get_available_etf_codes(复权类型)
            
            if not etf_codes:
                self.logger.error(f"❌ 未发现可用的ETF数据")
                return {"error": "无可用数据"}
            
            self.logger.info(f"📊 发现 {len(etf_codes)} 个ETF，开始加载数据...")
            etf_data = self.data_loader.load_multiple_etfs(etf_codes, 复权类型, days_back)
            
            if not etf_data:
                self.logger.error(f"❌ 数据加载失败")
                return {"error": "数据加载失败"}
            
            # 2. 执行筛选
            筛选结果 = self._run_filter_chain(etf_data)
            
            # 3. 生成最终结果
            最终结果 = self._generate_final_results(筛选结果)
            
            # 4. 统计摘要
            处理摘要 = self._generate_process_summary(etf_codes, etf_data, 筛选结果, 最终结果)
            
            return {
                "复权类型": 复权类型,
                "处理时间": datetime.now().isoformat(),
                "处理摘要": 处理摘要,
                "筛选结果": 筛选结果,
                "最终结果": 最终结果,
                "通过ETF": 最终结果["通过ETF列表"]
            }
    
    def _run_filter_chain(self, etf_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, FilterResult]]:
        """
        运行筛选器链
        
        Args:
            etf_data: ETF数据字典
        
        Returns:
            各筛选器的结果
        """
        筛选结果 = {}
        
        for filter_name, filter_obj in self.filters.items():
            self.logger.info(f"🔍 执行筛选器: {filter_name}")
            try:
                results = filter_obj.filter_multiple_etfs(etf_data)
                筛选结果[filter_name] = results
                
                # 记录筛选器统计
                stats = filter_obj.get_summary_stats(results)
                self.logger.log_stats(f"{filter_name}统计", stats)
                
            except Exception as e:
                self.logger.error(f"❌ 筛选器 {filter_name} 执行失败: {e}")
                筛选结果[filter_name] = {}
        
        return 筛选结果
    
    def _generate_final_results(self, 筛选结果: Dict[str, Dict[str, FilterResult]]) -> Dict[str, Any]:
        """
        生成最终筛选结果
        
        Args:
            筛选结果: 各筛选器的结果
        
        Returns:
            最终结果字典
        """
        if not 筛选结果:
            return {"通过ETF列表": [], "综合评分": {}}
        
        # 获取所有ETF代码
        all_etf_codes = set()
        for results in 筛选结果.values():
            all_etf_codes.update(results.keys())
        
        # 计算综合评分和通过情况
        综合评分 = {}
        通过统计 = {}
        
        for etf_code in all_etf_codes:
            etf_scores = {}
            etf_passed = {}
            
            for filter_name, results in 筛选结果.items():
                if etf_code in results:
                    result = results[etf_code]
                    etf_scores[filter_name] = result.score
                    etf_passed[filter_name] = result.passed
                else:
                    etf_scores[filter_name] = 0.0
                    etf_passed[filter_name] = False
            
            # 计算加权综合得分
            综合得分 = self._calculate_weighted_score(etf_scores)
            通过筛选器数 = sum(etf_passed.values())
            
            综合评分[etf_code] = {
                "综合得分": 综合得分,
                "各筛选器得分": etf_scores,
                "通过筛选器数": 通过筛选器数,
                "总筛选器数": len(self.filters),
                "通过率": 通过筛选器数 / len(self.filters) * 100,
                "各筛选器通过情况": etf_passed
            }
            
            通过统计[etf_code] = 通过筛选器数
        
        # 确定最终通过的ETF（需要通过所有筛选器）
        通过ETF列表 = [
            etf_code for etf_code, count in 通过统计.items() 
            if count == len(self.filters)
        ]
        
        # 按综合得分排序
        通过ETF列表.sort(key=lambda x: 综合评分[x]["综合得分"], reverse=True)
        
        return {
            "通过ETF列表": 通过ETF列表,
            "候选ETF列表": self._get_candidate_etfs(通过统计),
            "综合评分": 综合评分,
            "筛选统计": {
                "完全通过": len(通过ETF列表),
                "部分通过": len([k for k, v in 通过统计.items() if 0 < v < len(self.filters)]),
                "完全未通过": len([k for k, v in 通过统计.items() if v == 0]),
                "总ETF数": len(all_etf_codes)
            }
        }
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """
        计算加权综合得分
        
        Args:
            scores: 各筛选器得分
        
        Returns:
            加权综合得分
        """
        # 从配置文件读取权重设置
        weights = self.config.get_筛选器权重()
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for filter_name, score in scores.items():
            weight = weights.get(filter_name, 0.33)  # 默认权重
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _get_candidate_etfs(self, 通过统计: Dict[str, int]) -> List[str]:
        """
        获取候选ETF列表（通过1个筛选器但不是全部通过）
        
        Args:
            通过统计: ETF通过筛选器数量统计
        
        Returns:
            候选ETF列表
        """
        候选ETF = [
            etf_code for etf_code, count in 通过统计.items()
            if count >= 1 and count < len(self.filters)
        ]
        
        return sorted(候选ETF)
    
    def _generate_process_summary(self, all_etf_codes: List[str], 
                                etf_data: Dict[str, pd.DataFrame],
                                筛选结果: Dict[str, Dict[str, FilterResult]],
                                最终结果: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成处理摘要
        
        Args:
            all_etf_codes: 所有ETF代码
            etf_data: 加载的ETF数据
            筛选结果: 筛选结果
            最终结果: 最终结果
        
        Returns:
            处理摘要
        """
        return {
            "数据加载": {
                "发现ETF总数": len(all_etf_codes),
                "成功加载数": len(etf_data),
                "加载成功率": len(etf_data) / len(all_etf_codes) * 100 if all_etf_codes else 0
            },
            "筛选器执行": {
                "筛选器总数": len(self.filters),
                "执行成功数": len(筛选结果),
                "筛选器列表": list(self.filters.keys())
            },
            "筛选结果": 最终结果["筛选统计"],
            "数据质量": {
                "数据完整性": "良好" if len(etf_data) / len(all_etf_codes) > 0.9 else "一般",
                "数据时效性": "当日" if datetime.now().hour < 16 else "最新"
            }
        }
    
    def get_filter_descriptions(self) -> Dict[str, Any]:
        """获取所有筛选器的说明"""
        descriptions = {}
        for name, filter_obj in self.filters.items():
            if hasattr(filter_obj, 'get_filter_description'):
                descriptions[name] = filter_obj.get_filter_description()
        return descriptions
    
    def process_specific_etfs(self, etf_codes: List[str], 
                            复权类型: str = "0_ETF日K(前复权)",
                            days_back: int = None) -> Dict[str, Any]:
        """
        处理指定的ETF列表
        
        Args:
            etf_codes: 指定的ETF代码列表
            复权类型: 复权类型
            days_back: 加载最近N天的数据
        
        Returns:
            处理结果
        """
        self.logger.info(f"🎯 开始处理指定的 {len(etf_codes)} 个ETF")
        
        # 加载指定ETF的数据
        etf_data = self.data_loader.load_multiple_etfs(etf_codes, 复权类型, days_back)
        
        if not etf_data:
            return {"error": "指定ETF数据加载失败"}
        
        # 执行筛选
        筛选结果 = self._run_filter_chain(etf_data)
        最终结果 = self._generate_final_results(筛选结果)
        处理摘要 = self._generate_process_summary(etf_codes, etf_data, 筛选结果, 最终结果)
        
        return {
            "复权类型": 复权类型,
            "处理时间": datetime.now().isoformat(),
            "处理摘要": 处理摘要,
            "筛选结果": 筛选结果,
            "最终结果": 最终结果,
            "通过ETF": 最终结果["通过ETF列表"]
        } 