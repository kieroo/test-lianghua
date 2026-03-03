# 量化系统（Python）

这是一个轻量级的量化系统，支持：

- 行情数据读取（CSV OHLCV）
- 策略模块（均线交叉）
- 回测撮合（全仓买入 / 清仓卖出，含手续费）
- 绩效指标（收益率、年化、波动率、夏普、最大回撤）
- 在线行情（Binance Kline API）
- 在线交易（Binance Spot，下单支持 dry-run 与真实下单）

## 1) 本地回测

```bash
python3 run_backtest.py --data data/sample_ohlcv.csv --short-window 3 --long-window 8
```

## 2) 在线行情 + 在线交易循环

默认是 `dry-run`（不会真实下单）：

```bash
python3 run_live.py --symbol BTCUSDT --interval 1m --short-window 5 --long-window 20 --quantity 0.001 --iterations 3
```

真实下单模式（谨慎使用）：

```bash
export BINANCE_API_KEY='your_api_key'
export BINANCE_API_SECRET='your_api_secret'
python3 run_live.py --symbol BTCUSDT --interval 1m --quantity 0.001 --live --iterations 3
```

> 注意：请先确认交易所账户权限、最小下单数量、交易手续费与风控限制。建议先在小资金或测试环境验证。

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
