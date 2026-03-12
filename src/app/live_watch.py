# src/app/live_watch.py
# Polls MT5, rebuilds the state, and prints whether current skew is tradable.
from __future__ import annotations

import time

from src.broker.mt5_client import MT5Client
from src.common.logging import get_logger
from src.common.settings import load_settings
from src.data.history import load_pair_history
from src.strategy.features import build_feature_frame
from src.strategy.simulator import estimate_live_edge, simulate_trades


def main() -> None:
    cfg = load_settings()
    logger = get_logger("live", cfg.log_level)
    client = MT5Client(cfg)
    client.connect()
    last_bar_time = None
    try:
        meta_1 = client.symbol_meta(cfg.symbol_leg_1)
        meta_2 = client.symbol_meta(cfg.symbol_leg_2)
        while True:
            raw = load_pair_history(client, cfg.symbol_leg_1, cfg.symbol_leg_2, cfg.timeframe, cfg.history_bars)
            feat = build_feature_frame(raw, cfg)
            if feat.empty:
                time.sleep(cfg.live_poll_ms / 1000)
                continue
            current_bar_time = feat.iloc[-1].time
            if current_bar_time != last_bar_time:
                trades = simulate_trades(feat, cfg, meta_1, meta_2)
                live = estimate_live_edge(feat, trades, cfg)
                logger.info("time=%s live=%s", current_bar_time, live)
                last_bar_time = current_bar_time
            time.sleep(cfg.live_poll_ms / 1000)
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
