# -*- coding: utf-8 -*-
"""
LINE Messaging APIでの通知送信。
(LINE Notifyは2025年3月末で終了しているため、後継のMessaging APIを使用)

事前準備:
1. LINE公式アカウントを作成 (https://www.linebiz.com/jp/entry/)
2. LINE Developersコンソールでチャネル(Messaging API)を作成し、
   「チャネルアクセストークン(長期)」を発行する
3. スマホのLINEアプリで、作成した公式アカウントを友だち追加しておく
4. GitHub Actionsのsecretsに LINE_CHANNEL_ACCESS_TOKEN を登録する

送信方式はbroadcast(友だち全員に配信)を使用。
個人利用で自分だけが友だち登録している前提なら、実質的に自分専用の通知になる。
"""
import os
import requests

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


def send_line_broadcast(message: str) -> bool:
    """
    LINE Messaging APIのbroadcastエンドポイントでテキストメッセージを送る。
    トークンが未設定の場合は送信をスキップしてFalseを返す(ローカル検証用)。
    """
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        print("[notify] LINE_CHANNEL_ACCESS_TOKEN が未設定のため送信をスキップしました")
        return False

    # LINEの1メッセージは5000文字が上限。安全のため4500文字で切る
    if len(message) > 4500:
        message = message[:4500] + "\n...(以下省略)"

    resp = requests.post(
        LINE_BROADCAST_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        json={"messages": [{"type": "text", "text": message}]},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"[notify] LINE送信に失敗しました: status={resp.status_code} body={resp.text}")
        return False
    print("[notify] LINEへの通知を送信しました")
    return True
