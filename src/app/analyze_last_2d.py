# src/app/analyze_last_2d.py
# Runs the 2-day offline analysis and prints the first summary.
from __future__ import annotations

from pathlib import Path

from src.broker.mt5_client import MT5Client
from src.common.logging import get_logger
from src.common.settings import load_settings
from src.data.history import load_pair_history
from src.strategy.features import build_feature_frame
from src.strategy.simulator import estimate_live_edge, simulate_trades, summarize_trades


def main() -> None:
    cfg = load_settings()
    logger = get_logger("analyze", cfg.log_level)
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    client = MT5Client(cfg)
    client.connect()
    try:
        meta_1 = client.symbol_meta(cfg.symbol_leg_1)
        meta_2 = client.symbol_meta(cfg.symbol_leg_2)
        raw = load_pair_history(client, cfg.symbol_leg_1, cfg.symbol_leg_2, cfg.timeframe, cfg.history_bars)
        feat = build_feature_frame(raw, cfg)
        trades = simulate_trades(feat, cfg, meta_1, meta_2)
        summary = summarize_trades(trades)
        live = estimate_live_edge(feat, trades, cfg)
        raw.to_csv(Path(cfg.data_dir, "bars_last_2d.csv"), index=False)
        feat.to_csv(Path(cfg.data_dir, "features_last_2d.csv"), index=False)
        if not trades.empty:
            trades.to_csv(Path(cfg.data_dir, "trades_last_2d.csv"), index=False)
        logger.info("summary=%s", summary)
        logger.info("live=%s", live)
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
