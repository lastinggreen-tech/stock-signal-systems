# -*- coding: utf-8 -*-
"""
メイン実行スクリプト。GitHub Actionsから定期的に呼び出される想定。

処理の流れ:
1. watchlist.py の銘柄について yfinance で株価データを取得
2. indicators.py でテクニカル指標を計算
3. signals.py でBUY/SELL/NONEを判定
4. BUYまたはSELL(score>=1)が出た銘柄があればLINEへ通知
5. 全銘柄の状況を docs/index.html に書き出す(GitHub Pagesで公開)

実行方法:
    pip install -r requirements.txt
    python analyze.py
"""
import os
import sys
import time
import traceback

import pandas as pd
import yfinance as yf

from watchlist import WATCHLIST
from indicators import add_all_indicators
from signals import evaluate_signal
from notify import send_line_broadcast
from dashboard import build_dashboard_html

MIN_ROWS_REQUIRED = 80  # SMA75計算に必要な最低営業日数


def fetch_and_evaluate(code: str):
    """1銘柄分のデータ取得〜シグナル判定"""
    df = yf.download(code, period="9mo", interval="1d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise RuntimeError(f"{code}: データを取得できませんでした")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if len(df) < MIN_ROWS_REQUIRED:
        raise RuntimeError(f"{code}: データ件数が不足しています({len(df)}件)")

    df = add_all_indicators(df)
    result = evaluate_signal(df)
    return result


def main():
    results = []
    notify_lines = []

    for item in WATCHLIST:
        code, name = item["code"], item["name"]
        try:
            result = fetch_and_evaluate(code)
        except Exception as e:
            print(f"[warn] {code} ({name}) の処理でエラー: {e}", file=sys.stderr)
            traceback.print_exc()
            continue

        results.append({"code": code, "name": name, "result": result})

        if result["direction"] in ("BUY", "SELL"):
            direction_label = "🟢買いシグナル" if result["direction"] == "BUY" else "🔴売りシグナル"
            reasons = " / ".join(result["reasons"])
            notify_lines.append(
                f"{direction_label} {name}({code})\n"
                f"終値: {result['latest']['close']:.1f}\n"
                f"根拠: {reasons}"
            )

        time.sleep(1)

    if notify_lines:
        message = "【日本株テクニカルシグナル】\n\n" + "\n\n".join(notify_lines)
        send_line_broadcast(message)
    else:
        print("[info] 本日はシグナル該当銘柄がありませんでした")

    if results:
        os.makedirs("docs", exist_ok=True)
        html = build_dashboard_html(results)
        with open("docs/index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[info] ダッシュボードを docs/index.html に出力しました")
    else:
        print("[error] 全銘柄でデータ取得に失敗しました", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
