# -*- coding: utf-8 -*-
"""
ネットワーク接続なしで、指標計算とシグナル判定ロジックを検証するテスト。
合成データを使い、クロス発生の「その日」に正しくシグナルが検出されるかを確認する。
(急騰・急落が長期間続いた後はRSIが極端な水準になり、
 過熱警戒のSELL/BUY理由が優勢になるのは意図した挙動)
"""
import numpy as np
import pandas as pd

from indicators import add_all_indicators
from signals import evaluate_signal, _crossed_above, _crossed_below


def make_df(prices):
    idx = pd.date_range("2025-01-01", periods=len(prices), freq="B")
    return pd.DataFrame({"Close": prices}, index=idx)


def test_golden_cross_detected_at_the_moment_it_happens():
    np.random.seed(1)
    down = np.linspace(2000, 1500, 100) + np.random.normal(0, 2, 100)
    up = np.linspace(1500, 2000, 40) + np.random.normal(0, 2, 40)
    prices = np.concatenate([down, up])
    df = add_all_indicators(make_df(prices))

    # SMA5がSMA25を上抜けした「最初の日」を探す
    cross_day = None
    for i in range(30, len(df)):
        sub = df.iloc[: i + 1]
        if _crossed_above(sub["SMA5"], sub["SMA25"]):
            cross_day = i
            break
    assert cross_day is not None, "テストデータでゴールデンクロスが発生していない"

    result = evaluate_signal(df.iloc[: cross_day + 1])
    print("=== ゴールデンクロス発生日の判定 ===", result)
    assert result["direction"] == "BUY"
    assert any("ゴールデンクロス" in r for r in result["reasons"])


def test_dead_cross_detected_at_the_moment_it_happens():
    np.random.seed(2)
    up = np.linspace(1500, 2200, 100) + np.random.normal(0, 2, 100)
    down = np.linspace(2200, 1700, 40) + np.random.normal(0, 2, 40)
    prices = np.concatenate([up, down])
    df = add_all_indicators(make_df(prices))

    cross_day = None
    for i in range(30, len(df)):
        sub = df.iloc[: i + 1]
        if _crossed_below(sub["SMA5"], sub["SMA25"]):
            cross_day = i
            break
    assert cross_day is not None, "テストデータでデッドクロスが発生していない"

    result = evaluate_signal(df.iloc[: cross_day + 1])
    print("=== デッドクロス発生日の判定 ===", result)
    assert result["direction"] == "SELL"
    assert any("デッドクロス" in r for r in result["reasons"])


def test_rsi_basic_bounds():
    prices_up = np.linspace(1000, 1200, 60)
    df_up = add_all_indicators(make_df(prices_up))
    assert df_up["RSI14"].iloc[-1] > 60, f"単調上昇でRSIが低すぎる: {df_up['RSI14'].iloc[-1]}"

    prices_down = np.linspace(1200, 1000, 60)
    df_down = add_all_indicators(make_df(prices_down))
    assert df_down["RSI14"].iloc[-1] < 40, f"単調下落でRSIが高すぎる: {df_down['RSI14'].iloc[-1]}"
    print("=== RSI境界チェック ===")
    print("上昇トレンドRSI:", df_up["RSI14"].iloc[-1])
    print("下降トレンドRSI:", df_down["RSI14"].iloc[-1])


def test_overbought_state_flagged_as_caution():
    # 急騰が続きRSIが極端な水準に達した場合は、過熱警戒(SELL寄り)として
    # 検出されることを確認する(仕様として意図した挙動)
    np.random.seed(3)
    down = np.linspace(2000, 1500, 100) + np.random.normal(0, 2, 100)
    up = np.linspace(1500, 2000, 40) + np.random.normal(0, 2, 40)
    prices = np.concatenate([down, up])
    df = add_all_indicators(make_df(prices))
    result = evaluate_signal(df)
    print("=== 長期急騰後(最終日)の判定 ===", result)
    assert df["RSI14"].iloc[-1] > 70
    assert result["direction"] == "SELL"
    assert any("買われすぎ" in r for r in result["reasons"])


if __name__ == "__main__":
    test_golden_cross_detected_at_the_moment_it_happens()
    test_dead_cross_detected_at_the_moment_it_happens()
    test_rsi_basic_bounds()
    test_overbought_state_flagged_as_caution()
    print("\nすべてのロジックテストが完了しました（エラーなし）。")
