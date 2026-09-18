# -*- coding: utf-8 -*-
"""
売買シグナル判定ロジック。

考え方:
- ゴールデンクロス/デッドクロス(SMA5とSMA25)
- RSIの売られすぎ/買われすぎからの回復
- MACDのクロス
の3系統をそれぞれ判定し、複数が同時に成立するほど「強いシグナル」として扱う。

これは一般的なテクニカル分析の手法を組み合わせたものであり、
将来の値動きを保証するものではない。投資判断は自己責任で行うこと。
"""
import pandas as pd


def _crossed_above(series_a: pd.Series, series_b: pd.Series) -> bool:
    """直近の足でaがbを下から上に抜けたか"""
    if len(series_a) < 2 or len(series_b) < 2:
        return False
    prev_a, prev_b = series_a.iloc[-2], series_b.iloc[-2]
    curr_a, curr_b = series_a.iloc[-1], series_b.iloc[-1]
    if pd.isna(prev_a) or pd.isna(prev_b) or pd.isna(curr_a) or pd.isna(curr_b):
        return False
    return prev_a <= prev_b and curr_a > curr_b


def _crossed_below(series_a: pd.Series, series_b: pd.Series) -> bool:
    """直近の足でaがbを上から下に抜けたか"""
    if len(series_a) < 2 or len(series_b) < 2:
        return False
    prev_a, prev_b = series_a.iloc[-2], series_b.iloc[-2]
    curr_a, curr_b = series_a.iloc[-1], series_b.iloc[-1]
    if pd.isna(prev_a) or pd.isna(prev_b) or pd.isna(curr_a) or pd.isna(curr_b):
        return False
    return prev_a >= prev_b and curr_a < curr_b


def evaluate_signal(df: pd.DataFrame) -> dict:
    """
    指標計算済みのDataFrameを受け取り、直近時点でのシグナル判定結果を返す。

    戻り値:
        {
            "direction": "BUY" | "SELL" | "NONE",
            "score": int (1〜3, 一致した根拠の数),
            "reasons": [str, ...],
            "latest": {close, sma5, sma25, sma75, rsi14, macd, macd_signal}
        }
    """
    latest = df.iloc[-1]
    reasons_buy = []
    reasons_sell = []

    # 1) ゴールデンクロス/デッドクロス (SMA5 x SMA25)
    if _crossed_above(df["SMA5"], df["SMA25"]):
        reasons_buy.append("ゴールデンクロス(SMA5がSMA25を上抜け)")
    if _crossed_below(df["SMA5"], df["SMA25"]):
        reasons_sell.append("デッドクロス(SMA5がSMA25を下抜け)")

    # 2) RSIの売られすぎ/買われすぎからの回復
    rsi_series = df["RSI14"]
    if len(rsi_series) >= 2 and not pd.isna(rsi_series.iloc[-2]) and not pd.isna(rsi_series.iloc[-1]):
        if rsi_series.iloc[-2] < 30 <= rsi_series.iloc[-1]:
            reasons_buy.append("RSIが30を上抜け(売られすぎからの反発)")
        if rsi_series.iloc[-2] > 70 >= rsi_series.iloc[-1]:
            reasons_sell.append("RSIが70を下抜け(買われすぎからの反落)")
        if rsi_series.iloc[-1] >= 70:
            reasons_sell.append(f"RSIが買われすぎ水準({rsi_series.iloc[-1]:.1f})")
        if rsi_series.iloc[-1] <= 30:
            reasons_buy.append(f"RSIが売られすぎ水準({rsi_series.iloc[-1]:.1f})")

    # 3) MACDクロス
    if _crossed_above(df["MACD"], df["MACD_SIGNAL"]):
        reasons_buy.append("MACDがシグナルを上抜け(ゴールデンクロス)")
    if _crossed_below(df["MACD"], df["MACD_SIGNAL"]):
        reasons_sell.append("MACDがシグナルを下抜け(デッドクロス)")

    latest_info = {
        "close": float(latest["Close"]),
        "sma5": None if pd.isna(latest.get("SMA5")) else float(latest["SMA5"]),
        "sma25": None if pd.isna(latest.get("SMA25")) else float(latest["SMA25"]),
        "sma75": None if pd.isna(latest.get("SMA75")) else float(latest["SMA75"]),
        "rsi14": None if pd.isna(latest.get("RSI14")) else float(latest["RSI14"]),
        "macd": None if pd.isna(latest.get("MACD")) else float(latest["MACD"]),
        "macd_signal": None if pd.isna(latest.get("MACD_SIGNAL")) else float(latest["MACD_SIGNAL"]),
    }

    if len(reasons_buy) >= len(reasons_sell) and reasons_buy:
        return {
            "direction": "BUY",
            "score": len(reasons_buy),
            "reasons": reasons_buy,
            "latest": latest_info,
        }
    if reasons_sell:
        return {
            "direction": "SELL",
            "score": len(reasons_sell),
            "reasons": reasons_sell,
            "latest": latest_info,
        }
    return {"direction": "NONE", "score": 0, "reasons": [], "latest": latest_info}
