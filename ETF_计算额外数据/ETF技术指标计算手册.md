# ETF技术指标计算手册

## 现有数据字段
基于当前ETF数据包含的字段：
- **代码**: ETF代码
- **日期**: 交易日期  
- **开盘价**: 当日开盘价格
- **最高价**: 当日最高价格
- **最低价**: 当日最低价格
- **收盘价**: 当日收盘价格
- **上日收盘**: 前一交易日收盘价
- **涨跌**: 当日涨跌金额
- **涨幅%**: 当日涨跌幅百分比
- **成交量(手数)**: 当日成交量
- **成交额(千元)**: 当日成交金额

---

## 可计算的技术指标清单

### 1. 趋势类指标

#### 1.1 移动平均线 (Moving Average)
- **SMA_5**: 5日简单移动平均线
- **SMA_10**: 10日简单移动平均线
- **SMA_20**: 20日简单移动平均线
- **SMA_60**: 60日简单移动平均线
- **SMA_120**: 120日简单移动平均线
- **SMA_250**: 250日简单移动平均线

#### 1.2 指数移动平均线 (Exponential Moving Average)
- **EMA_12**: 12日指数移动平均线
- **EMA_26**: 26日指数移动平均线
- **EMA_9**: 9日指数移动平均线

#### 1.3 加权移动平均线 (Weighted Moving Average)
- **WMA_5**: 5日加权移动平均线
- **WMA_10**: 10日加权移动平均线
- **WMA_20**: 20日加权移动平均线

#### 1.4 MACD指标组合
- **DIF**: 差离值 (EMA_12 - EMA_26)
- **DEA**: 信号线 (DIF的9日EMA)
- **MACD**: MACD柱 (DIF - DEA) × 2
- **MACD_Signal**: MACD信号 (金叉/死叉)

### 2. 波动性指标

#### 2.1 布林带 (Bollinger Bands)
- **BB_Middle**: 中轨 (20日SMA)
- **BB_Upper**: 上轨 (中轨 + 2×标准差)
- **BB_Lower**: 下轨 (中轨 - 2×标准差)
- **BB_Width**: 带宽 ((上轨-下轨)/中轨)
- **BB_Position**: 价格位置 ((收盘价-下轨)/(上轨-下轨))

#### 2.2 真实波幅 (Average True Range)
- **TR**: 真实波幅 = MAX(高-低, |高-昨收|, |低-昨收|)
- **ATR_14**: 14日平均真实波幅
- **ATR_21**: 21日平均真实波幅

#### 2.3 波动率指标
- **Volatility_20**: 20日历史波动率
- **Price_Range**: 当日振幅 ((最高价-最低价)/昨收盘×100%)

### 3. 相对强弱指标

#### 3.1 RSI (Relative Strength Index)
- **RSI_6**: 6日相对强弱指数
- **RSI_12**: 12日相对强弱指数
- **RSI_14**: 14日相对强弱指数
- **RSI_24**: 24日相对强弱指数

#### 3.2 威廉指标 (Williams %R)
- **WR_14**: 14日威廉指标
- **WR_21**: 21日威廉指标
- **计算公式**: (最高价-收盘价)/(最高价-最低价) × 100

### 4. 成交量指标

#### 4.1 成交量移动平均线
- **Volume_MA_5**: 5日成交量均线
- **Volume_MA_10**: 10日成交量均线
- **Volume_MA_20**: 20日成交量均线
- **Volume_MA_60**: 60日成交量均线

#### 4.2 量价指标
- **OBV**: 能量潮指标
- **Volume_Ratio**: 量比 (当日成交量/近期平均成交量)
- **Turnover_Rate_Base**: 换手率基础数据 (需要流通股本)
- **Amount_MA_5**: 5日成交额均线
- **Amount_MA_10**: 10日成交额均线

#### 4.3 价量配合度
- **Price_Volume_Correlation**: 价量相关性
- **Volume_Price_Trend**: 量价趋势指标

### 5. 动量指标

#### 5.1 KDJ指标
- **K_Value**: K值
- **D_Value**: D值  
- **J_Value**: J值 (3×K - 2×D)
- **KDJ_Signal**: KDJ信号

#### 5.2 CCI指标 (Commodity Channel Index)
- **CCI_14**: 14日顺势指标
- **CCI_20**: 20日顺势指标
- **Typical_Price**: 典型价格 ((最高价+最低价+收盘价)/3)

#### 5.3 动量振荡器
- **Momentum_10**: 10日动量
- **ROC_12**: 12日变动率

### 6. 支撑阻力指标

#### 6.1 枢轴点 (Pivot Point)
- **Pivot_Point**: 枢轴点 ((最高价+最低价+收盘价)/3)
- **Support_1**: 第一支撑位 (2×PP - 最高价)
- **Support_2**: 第二支撑位 (PP - (最高价-最低价))
- **Resistance_1**: 第一阻力位 (2×PP - 最低价)
- **Resistance_2**: 第二阻力位 (PP + (最高价-最低价))

#### 6.2 价格通道
- **Donchian_Upper**: 唐奇安上轨 (N日最高价)
- **Donchian_Lower**: 唐奇安下轨 (N日最低价)

### 7. 市场结构指标

#### 7.1 缺口分析
- **Gap_Up**: 向上缺口 (当日最低价 > 昨日最高价)
- **Gap_Down**: 向下缺口 (当日最高价 < 昨日最低价)
- **Gap_Size**: 缺口大小
- **Gap_Fill**: 缺口回补状态

#### 7.2 K线形态识别
- **Doji**: 十字星形态
- **Hammer**: 锤子线形态
- **Hanging_Man**: 上吊线形态
- **Engulfing_Bullish**: 看涨吞没形态
- **Engulfing_Bearish**: 看跌吞没形态
- **Inside_Bar**: 内包线形态
- **Outside_Bar**: 外包线形态

#### 7.3 价格形态
- **Higher_High**: 更高高点
- **Higher_Low**: 更高低点
- **Lower_High**: 更低高点
- **Lower_Low**: 更低低点

### 8. 统计类指标

#### 8.1 收益率序列
- **Daily_Return**: 日收益率 ((今收盘-昨收盘)/昨收盘)
- **Cumulative_Return**: 累计收益率
- **Weekly_Return**: 周收益率
- **Monthly_Return**: 月收益率
- **Annualized_Return**: 年化收益率

#### 8.2 波动率统计
- **Volatility_Daily**: 日波动率
- **Volatility_Weekly**: 周波动率
- **Volatility_Monthly**: 月波动率
- **Sharpe_Ratio_Base**: 夏普比率基础数据

#### 8.3 统计描述
- **Max_Price_20**: 20日最高价
- **Min_Price_20**: 20日最低价
- **Price_Percentile**: 价格分位数
- **Average_Amplitude**: 平均振幅

### 9. 复权相关指标

#### 9.1 复权价格对比
- **Forward_Backward_Diff**: 前复权与后复权价差
- **Adjusted_Raw_Ratio**: 复权价格与原始价格比率
- **Adjustment_Factor_Change**: 复权因子变化率

#### 9.2 复权分析
- **Dividend_Impact**: 分红影响分析
- **Split_Impact**: 拆股影响分析

### 10. 流动性指标 (部分可计算)

#### 10.1 可计算的流动性指标
- **Turnover_Velocity**: 成交活跃度 (成交额/平均成交额)
- **Volume_Weighted_Price**: 成交量加权平均价格 (VWAP)
- **Time_Weighted_Volume**: 时间加权成交量

#### 10.2 需要额外数据的指标
- **Turnover_Rate**: 换手率 (需要流通股本)
- **Market_Cap_Ratio**: 市值比率 (需要总市值)

---

## 计算优先级建议

### 🔥 第一优先级 (核心技术指标)
1. 移动平均线 (MA5, MA10, MA20, MA60)
2. MACD指标组合
3. RSI指标 (RSI14)
4. 布林带
5. 成交量均线

### ⭐ 第二优先级 (技术分析增强)
1. KDJ指标
2. ATR波动率
3. 威廉指标 (%R)
4. OBV能量潮
5. 收益率计算
6. 枢轴点支撑阻力

### 📊 第三优先级 (高级分析)
1. CCI指标
2. K线形态识别
3. 缺口分析
4. 波动率统计
5. 复权对比分析

---

## 使用示例

```python
# 获取ETF所有技术指标
analyzer = ETFTechnicalAnalyzer('159001')
indicators = analyzer.get_all_indicators()

# 访问具体指标
ma20 = indicators['趋势指标']['SMA_20']
rsi14 = indicators['强弱指标']['RSI_14']
bb_upper = indicators['波动性指标']['BB_Upper']
```

---

## 备注说明

1. **数据依赖**: 所有指标基于现有的OHLCV数据计算
2. **计算周期**: 建议保留至少250个交易日的数据以支持长周期指标
3. **实时更新**: 可以结合日更/周更系统自动计算新指标
4. **扩展性**: 框架支持添加新的自定义指标
5. **复权选择**: 建议使用前复权数据进行技术分析 