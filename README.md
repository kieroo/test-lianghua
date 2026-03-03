# 量化系统（Python）

这是一个轻量级的量化回测系统，包含：

- 行情数据读取（CSV OHLCV）
- 策略模块（均线交叉）
- 回测撮合（全仓买入 / 清仓卖出，含手续费）
- 绩效指标（收益率、年化、波动率、夏普、最大回撤）
- 命令行执行入口 + 示例数据

## 快速开始

```bash
python3 run_backtest.py --data data/sample_ohlcv.csv --short-window 3 --long-window 8
```

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
- 接入真实交易所 API 或数据库
- 增加参数寻优与 walk-forward 分析
