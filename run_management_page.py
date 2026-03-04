#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict

from quant_system.management import ManagementService


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("请先安装 streamlit: pip install streamlit") from exc

    st.set_page_config(page_title="量化管理页面", layout="wide")
    st.title("量化交易管理页面")

    if "manager" not in st.session_state:
        st.session_state.manager = ManagementService()
    manager: ManagementService = st.session_state.manager

    tab_backtest, tab_strategy, tab_positions, tab_orders = st.tabs(["回测", "策略参数", "持仓", "下单"])

    with tab_backtest:
        st.subheader("回测")
        data_path = st.text_input("数据文件路径", value="data/sample_ohlcv.csv")
        capital = st.number_input("初始资金", min_value=1000.0, value=100000.0, step=1000.0)
        fee_rate = st.number_input("手续费率", min_value=0.0, max_value=0.01, value=0.0005, step=0.0001, format="%.4f")
        settlement = st.selectbox("结算制度", options=["T+0", "T+1"])

        if st.button("执行回测", use_container_width=True):
            try:
                backtest = manager.run_backtest(
                    data_path=data_path,
                    capital=capital,
                    fee_rate=fee_rate,
                    settlement=settlement,
                )
                m = backtest["metrics"]
                c1, c2, c3 = st.columns(3)
                c1.metric("最终净值", f"{backtest['final_equity']:.2f}")
                c2.metric("总收益", f"{m.total_return:.2%}")
                c3.metric("夏普", f"{m.sharpe_ratio:.3f}")
                st.caption(f"数据点数量: {backtest['data_points']}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"回测失败: {exc}")

    with tab_strategy:
        st.subheader("策略参数")
        current = manager.strategy_config
        strategy_name = st.selectbox("策略", options=["adaptive", "ma"], index=0 if current.strategy_name == "adaptive" else 1)
        short_window = st.number_input("短均线窗口", min_value=1, value=current.short_window, step=1)
        long_window = st.number_input("长均线窗口", min_value=2, value=current.long_window, step=1)

        if st.button("更新策略", use_container_width=True):
            try:
                config = manager.update_strategy(strategy_name, int(short_window), int(long_window))
                st.success(f"已更新: {asdict(config)}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"更新失败: {exc}")

    with tab_positions:
        st.subheader("当前持仓")
        st.metric("可用现金", f"{manager.cash:.2f}")
        positions = manager.list_positions()
        if positions:
            st.dataframe([asdict(p) for p in positions], use_container_width=True)
        else:
            st.info("暂无持仓")

    with tab_orders:
        st.subheader("手动下单")
        symbol = st.text_input("交易对/代码", value="BTCUSDT")
        side = st.selectbox("方向", options=["BUY", "SELL"])
        quantity = st.number_input("数量", min_value=0.0001, value=0.01, step=0.01, format="%.4f")
        price = st.number_input("价格", min_value=0.0001, value=30000.0, step=10.0, format="%.4f")

        if st.button("提交订单", use_container_width=True):
            try:
                execution = manager.place_order(symbol=symbol, side=side, quantity=float(quantity), price=float(price))
                st.success(f"下单成功: {asdict(execution)}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"下单失败: {exc}")

        st.markdown("#### 订单记录")
        executions = manager.list_executions()
        if executions:
            st.dataframe([asdict(e) for e in executions], use_container_width=True)
        else:
            st.info("暂无订单")


if __name__ == "__main__":
    main()
