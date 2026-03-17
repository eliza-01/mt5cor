from __future__ import annotations

import argparse

from src.app.ui_relative_compare.services.market.loaders import load_two_symbols
from src.app.ui_relative_compare.services.market.hedge import analyze_pair_hedge, build_spread_trade_directions
from src.common.settings import load_settings
from src.broker.mt5_client import MT5Client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect hedge ratio and spread diagnostics for a pair")
    parser.add_argument("--symbol-1", required=True)
    parser.add_argument("--symbol-2", required=True)
    parser.add_argument("--timeframe", default="M1")
    parser.add_argument("--bars", type=int, default=1500)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = load_settings()
    client = MT5Client(cfg)
    client.connect()
    try:
        frame, meta_1, meta_2 = load_two_symbols(
            client=client,
            symbol_1=args.symbol_1,
            symbol_2=args.symbol_2,
            timeframe=args.timeframe,
            bars=args.bars,
        )
        result = analyze_pair_hedge(
            close_1=frame["close_1"],
            close_2=frame["close_2"],
            symbol_1=args.symbol_1,
            symbol_2=args.symbol_2,
            meta_1=meta_1,
            meta_2=meta_2,
        )
        spread_side, side_1, side_2 = build_spread_trade_directions(
            spread_z=result.spread.zscore,
            side_relation=result.side_relation,
        )

        print(f"window={result.window}")
        print(f"symbol_1={args.symbol_1} mode={result.conversion_mode_1}")
        print(f"symbol_2={args.symbol_2} mode={result.conversion_mode_2}")
        print(f"corr={result.correlation:+.6f}")
        print(f"q_exec={result.execution_ratio:+.6f}")
        print(f"q_exec_abs={result.execution_ratio_abs:.6f}")
        print(f"side_relation={result.side_relation}")
        print(f"spread_beta={result.spread.beta:+.6f}")
        print(f"spread_intercept={result.spread.intercept:+.6f}")
        print(f"spread_last={result.spread.last:+.6f}")
        print(f"spread_z={result.spread.zscore:+.6f}")
        print(f"coint_pvalue={result.spread.coint_pvalue}")
        print(f"adf_pvalue={result.spread.adf_pvalue}")
        print(f"trade={spread_side} spread -> {side_1.upper()} {args.symbol_1} / {side_2.upper()} {args.symbol_2}")
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
