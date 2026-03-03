# 量化系统（Python）

这是一个轻量级的量化系统，支持：

- 行情数据读取（CSV OHLCV）
- 策略模块（均线交叉）
- 回测撮合（全仓买入 / 清仓卖出，含手续费）
- 绩效指标（收益率、年化、波动率、夏普、最大回撤）
- 在线行情：
  - Binance Kline API（加密市场）
  - Yahoo Finance Chart API（美股市场）
- 在线交易（Binance Spot，下单支持 dry-run 与真实下单）
- 交易制度约束（T+0 / T+1，适用于回测与在线循环信号执行）

## 1) 本地回测

```bash
python3 run_backtest.py --data data/sample_ohlcv.csv --short-window 3 --long-window 8
```

如需在回测中使用 T+1 约束，可在代码中初始化：

```python
Backtester(initial_capital=100000, fee_rate=0.001, settlement="T+1")
```

## 2) 在线行情 + 在线交易循环

### 2.1 加密市场（Binance）

默认是 `dry-run`（不会真实下单）：

```bash
python3 run_live.py --market crypto --symbol BTCUSDT --interval 1m --short-window 5 --long-window 20 --quantity 0.001 --iterations 3 --settlement T+0
```

真实下单模式（谨慎使用）：

```bash
export BINANCE_API_KEY='your_api_key'
export BINANCE_API_SECRET='your_api_secret'
python3 run_live.py --market crypto --symbol BTCUSDT --interval 1m --quantity 0.001 --live --iterations 3 --settlement T+0
```

### 2.2 美股市场（Yahoo 数据，dry-run）

```bash
python3 run_live.py --market us --symbol AAPL --interval 1d --short-window 5 --long-window 20 --quantity 1 --iterations 3 --settlement T+1
```

> 当前 `--market us` 仅支持 dry-run 信号执行，不进行真实券商下单。

## CSV 格式

必须包含以下列：

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`

## 测试

```bash
python3 -m pytest -q
```

## 可扩展方向

- 增加多资产组合与仓位管理
- 增加风险控制（止损、风控阈值）
- 增加 websocket 实时订阅，避免轮询延迟
- 增加参数寻优与 walk-forward 分析
