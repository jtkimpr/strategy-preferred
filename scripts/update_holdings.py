"""
Strategy Dashboard — BTC 보유량 및 MSTR 발행주식수 자동 업데이트
- BTC 보유량: SEC EDGAR 최신 8-K 공시 파싱
- MSTR 발행주식수: Finnhub profile API (수일 지연 가능성 있음)
"""

import csv
import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
today = datetime.now(KST).strftime("%Y-%m-%d")

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SEC_USER_AGENT = "strategy-dashboard/1.0 contact@example.com"


def read_csv_latest(filename):
    """CSV 파일의 마지막 행(최신값) 반환"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None, None
    last = rows[-1]
    return last["date"], float(last[list(last.keys())[1]])


def append_csv_if_changed(filename, date, new_value, col_name, allow_decrease=False):
    """최신값과 다를 때만 CSV에 행 추가"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    latest_val = float(rows[-1][col_name]) if rows else None

    if latest_val is not None and int(new_value) == int(latest_val):
        print(f"{filename}: 변화 없음 ({int(new_value):,}) — 스킵")
        return False

    # 주식수·보유량이 이전보다 감소하면 데이터 이상으로 간주 → 스킵 (부채는 예외)
    if not allow_decrease and latest_val is not None and int(new_value) < int(latest_val):
        print(f"{filename}: 신규값({int(new_value):,})이 현재값({int(latest_val):,})보다 낮음 — 데이터 이상, 스킵")
        return False

    rows.append({"date": date, col_name: int(new_value)})
    rows.sort(key=lambda x: x["date"])

    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", col_name])
        writer.writeheader()
        writer.writerows(rows)

    action = "추가" if not any(r["date"] == date for r in rows[:-1]) else "업데이트"
    print(f"{filename}: {int(new_value):,} ({action})")
    return True


def fetch_btc_holdings_from_edgar():
    """SEC EDGAR 최신 8-K에서 Strategy BTC 누적 보유량 파싱"""
    cik = "1050446"
    sub_url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    req = urllib.request.Request(sub_url, headers={"User-Agent": SEC_USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as res:
        data = json.loads(res.read())

    recent = data["filings"]["recent"]

    for i, form in enumerate(recent["form"]):
        if form != "8-K":
            continue

        accession = recent["accessionNumber"][i]
        primary_doc = recent["primaryDocument"][i]
        accession_nodash = accession.replace("-", "")
        filing_date = recent["filingDate"][i]

        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/{primary_doc}"
        req2 = urllib.request.Request(doc_url, headers={"User-Agent": SEC_USER_AGENT})
        with urllib.request.urlopen(req2, timeout=15) as res2:
            text = res2.read().decode("utf-8", errors="ignore")

        clean = re.sub(r'<[^>]+>', ' ', text)
        clean = re.sub(r'&#160;', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean)

        # "BTC Update" 섹션 찾기
        btc_update = re.search(r'BTC Update(.{0,800})', clean, re.IGNORECASE)
        if not btc_update:
            continue

        section = btc_update.group(1)
        # 6자리 누적 보유량 (예: 738,731)
        cumulative = re.findall(r'\b(\d{3},\d{3})\b', section)
        if cumulative:
            holdings = int(cumulative[-1].replace(",", ""))
            return filing_date, holdings

    raise ValueError("최신 8-K에서 BTC 보유량을 찾을 수 없음")


def fetch_mstr_debt_from_edgar():
    """SEC EDGAR XBRL에서 Strategy 총 금융부채(LongTermDebt) 조회"""
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001050446.json"
    req = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read())

    lt_debt_entries = (
        data.get("facts", {})
            .get("us-gaap", {})
            .get("LongTermDebt", {})
            .get("units", {})
            .get("USD", [])
    )
    if not lt_debt_entries:
        raise ValueError("EDGAR XBRL에서 LongTermDebt 데이터를 찾을 수 없음")

    # 10-K / 10-Q 연간·분기 보고서 기준, 가장 최근 기간 종료일 기준으로 선택
    quarterly = [
        e for e in lt_debt_entries
        if e.get("form") in ("10-K", "10-Q") and e.get("end") and e.get("val") is not None
    ]
    if not quarterly:
        raise ValueError("10-K/10-Q 부채 데이터 없음")

    quarterly.sort(key=lambda x: (x["end"], x.get("filed", "")))
    latest = quarterly[-1]
    return latest["end"], int(latest["val"])


def fetch_mstr_shares_from_finnhub():
    """Finnhub에서 MSTR 발행주식수 조회 (수일 지연 가능)"""
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol=MSTR&token={FINNHUB_API_KEY}"
    with urllib.request.urlopen(url, timeout=10) as res:
        profile = json.loads(res.read())
    shares = profile.get("shareOutstanding", 0)
    if not shares:
        raise ValueError("Finnhub에서 shareOutstanding 값을 가져오지 못함")
    return int(shares * 1_000_000)


def main():
    errors = []

    # 1. BTC 보유량
    print("=== BTC 보유량 업데이트 (SEC EDGAR) ===")
    try:
        filing_date, holdings = fetch_btc_holdings_from_edgar()
        append_csv_if_changed("btc_holdings.csv", filing_date, holdings, "holdings")
    except Exception as e:
        print(f"[오류] BTC 보유량: {e}")
        errors.append("btc_holdings")

    # 2. MSTR 발행주식수
    print("\n=== MSTR 발행주식수 업데이트 (Finnhub) ===")
    try:
        shares = fetch_mstr_shares_from_finnhub()
        append_csv_if_changed("mstr_shares.csv", today, shares, "shares")
    except Exception as e:
        print(f"[오류] MSTR 주식수: {e}")
        errors.append("mstr_shares")

    # 3. 총 금융부채
    print("\n=== 총 금융부채 업데이트 (SEC EDGAR XBRL) ===")
    try:
        debt_date, debt = fetch_mstr_debt_from_edgar()
        append_csv_if_changed("mstr_debt.csv", debt_date, debt, "debt", allow_decrease=True)
    except Exception as e:
        print(f"[오류] 금융부채: {e}")
        errors.append("mstr_debt")

    if errors:
        print(f"\n실패 항목: {', '.join(errors)}")
        exit(1)
    else:
        print("\n완료")


if __name__ == "__main__":
    main()
