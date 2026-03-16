"""
Strategy Dashboard — 가격 자동 업데이트 스크립트
GitHub Actions에서 하루 2회 실행 (00:00, 12:00 KST)
"""

import csv
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

# KST 기준 오늘 날짜
KST = timezone(timedelta(hours=9))
today = datetime.now(KST).strftime("%Y-%m-%d")

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_finnhub(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.loads(res.read())
    price = data.get("c", 0)
    if not price or price == 0:
        raise ValueError(f"{ticker} 가격 0 반환 (장 휴장 또는 오류)")
    return round(price, 4)


def fetch_btc():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.loads(res.read())
    price = data["bitcoin"]["usd"]
    if not price or price == 0:
        raise ValueError("BTC 가격 0 반환")
    return round(price, 2)


def update_csv(filename, price):
    path = os.path.join(DATA_DIR, filename)
    rows = []

    # 기존 데이터 읽기
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 오늘 날짜 행이 있으면 업데이트, 없으면 추가
    existing = next((r for r in rows if r["date"] == today), None)
    if existing:
        existing["price"] = price
        action = "업데이트"
    else:
        rows.append({"date": today, "price": price})
        action = "추가"

    # 날짜 오름차순 정렬 후 저장
    rows.sort(key=lambda x: x["date"])
    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "price"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{today}] {filename}: {price} ({action})")


def main():
    tasks = [
        ("btc.csv",  "BTC",  fetch_btc),
        ("mstr.csv", "MSTR", lambda: fetch_finnhub("MSTR")),
        ("strf.csv", "STRF", lambda: fetch_finnhub("STRF")),
        ("strk.csv", "STRK", lambda: fetch_finnhub("STRK")),
        ("strc.csv", "STRC", lambda: fetch_finnhub("STRC")),
        ("strd.csv", "STRD", lambda: fetch_finnhub("STRD")),
    ]

    errors = []
    for filename, ticker, fetch_fn in tasks:
        try:
            price = fetch_fn()
            update_csv(filename, price)
        except Exception as e:
            print(f"[오류] {ticker}: {e}")
            errors.append(ticker)

    if errors:
        print(f"\n실패 티커: {', '.join(errors)}")
        exit(1)
    else:
        print("\n모든 데이터 업데이트 완료")


if __name__ == "__main__":
    main()
