# Strategy Dashboard — 프로젝트 계획서

> 최초 작성: 2026-03-15
> 최종 업데이트: 2026-03-16

---

## 1. 프로젝트 개요

미국 증시에 상장된 Strategy 관련 유가증권과 BTC의 가격을 추적하고,
커스텀 지표(mNAV)를 시각적 그래프로 보여주는 웹 대시보드 구축.

- **접속 주소**: `https://jtkimpr.github.io/strategy-preferred`
- **호스팅**: GitHub Pages (Public 레포)
- **개발 환경**: MacBook Pro, Claude Code CLI, GitHub 동기화
- **로컬 미리보기**: `python3 -m http.server 8080` → `http://localhost:8080`

---

## 2. 추적 대상

| 티커 | 종류 | 데이터 출처 |
|------|------|------------|
| BTC  | 암호화폐 | CoinGecko API |
| MSTR | 보통주 | Finnhub API |
| STRF | 우선주 | Finnhub API |
| STRK | 우선주 | Finnhub API |
| STRC | 우선주 | Finnhub API |
| STRD | 우선주 | Finnhub API |

---

## 3. 핵심 지표: mNAV

### 계산식

```
mNAV = MSTR 시가총액 ÷ (BTC 보유량 × BTC 가격 − 총 금융부채)
```

- **분자**: MSTR 주가 × 발행주식수
- **분모**: BTC 순자산 가치 (BTC 가치에서 부채 차감)
- 1.0 = BTC 순자산과 동일 가치 / 역사적 범위: 약 1.5x ~ 3.5x
- strategy.com 기준과 동일한 방식 (부채 차감 적용)

### 데이터 소스 및 주의사항

| 항목 | 파일 | 출처 | 업데이트 주기 |
|------|------|------|-------------|
| BTC 보유량 | `btc_holdings.csv` | SEC EDGAR 8-K | 매수 공시 시 |
| 발행주식수 | `mstr_shares.csv` | Finnhub profile2 | 분기 (수일 지연) |
| 총 금융부채 | `mstr_debt.csv` | SEC EDGAR XBRL | 분기 (10-K/10-Q) |

- 부채 데이터는 분기 공시 기준 → 최신 발행 부채와 차이 발생 가능
- Q1 2026 10-Q 공시(5월경) 후 자동 수렴 예정

---

## 4. 파일 구조

```
strategy-preferred/
├── index.html                          # 대시보드 메인 페이지
├── data/
│   ├── btc.csv                         # BTC 일별 가격
│   ├── mstr.csv                        # MSTR 일별 가격
│   ├── strf.csv / strk.csv / strc.csv / strd.csv
│   ├── btc_holdings.csv                # BTC 누적 보유량 이력 (매수 이벤트)
│   ├── mstr_shares.csv                 # MSTR 발행주식수 이력 (분기)
│   └── mstr_debt.csv                   # 총 금융부채 이력 (분기)
├── scripts/
│   ├── update_prices.py                # 가격 데이터 자동 업데이트
│   └── update_holdings.py              # 보유량·주식수·부채 자동 업데이트
└── .github/workflows/
    ├── update-prices.yml               # 하루 2회 (00:00, 12:00 KST)
    └── update-holdings.yml             # 하루 1회 (00:00 KST)
```

### CSV 형식

```
date,price          ← 가격 파일 (YYYY-MM-DD, 소수점 가격)
date,holdings       ← btc_holdings.csv (누적 BTC 수량)
date,shares         ← mstr_shares.csv (발행주식수)
date,debt           ← mstr_debt.csv (총 부채, USD 단위)
```

---

## 5. GitHub Actions 스케줄

| 워크플로우 | 실행 시간 (KST) | 실행 스크립트 |
|-----------|----------------|-------------|
| `update-prices.yml` | 00:00, 12:00 (월~금) | `update_prices.py` |
| `update-holdings.yml` | 00:00 (월~금) | `update_holdings.py` |

- GitHub Secret: `FINNHUB_API_KEY` 등록 필요
- 수동 실행: GitHub → Actions → 워크플로우 선택 → "Run workflow"

---

## 6. 스크립트 동작

### update_prices.py
- Finnhub: MSTR/STRF/STRK/STRC/STRD 종가 조회
- CoinGecko: BTC 종가 조회
- 오늘 날짜 행 추가 (이미 있으면 업데이트)
- 가격 0이면 스킵

### update_holdings.py
1. **BTC 보유량**: SEC EDGAR 최신 8-K 파싱 ("BTC Update" 섹션 → 6자리 숫자)
2. **발행주식수**: Finnhub profile2 API (`shareOutstanding × 1,000,000`)
3. **총 금융부채**: SEC EDGAR XBRL (`LongTermDebt`, 10-K/10-Q 기준)
- 보유량·주식수는 감소 시 이상 데이터로 간주 → 스킵
- 부채는 감소 허용 (상환 가능)

---

## 7. 대시보드 UI 구성

1. **mNAV 계산 기준 bar** — 최신 BTC 보유량 / 발행주식수 / 총 금융부채 표시
2. **가격 카드 (7개)** — mNAV / BTC / MSTR / STRF / STRK / STRC / STRD
3. **성과 비교 차트** — 첫 거래일 = 100 기준 정규화, 7개 시리즈
4. **mNAV 차트** — 부채 차감 기준 프리미엄 추이
5. **개별 가격 차트 (6개)** — 3열 반응형 그리드

### 색상 코드
```javascript
mnav: '#facc15'  // 밝은 노란색
btc:  '#f7931a'  // 비트코인 오렌지
mstr: '#ff6b35'  // 레드오렌지
strf: '#2196f3'  // 파란색
strk: '#a855f7'  // 보라색
strc: '#4caf50'  // 초록색
strd: '#e91e63'  // 핑크
```

### 차트 동기화
- 모든 차트는 시간축 드래그 시 동기화 (`subscribeVisibleLogicalRangeChange`)

---

## 8. 기술 스택

| 항목 | 선택 |
|------|------|
| 차트 | TradingView Lightweight Charts v4.2.0 (CDN) |
| 데이터 | CSV 파일 (fetch로 직접 로드) |
| 호스팅 | GitHub Pages |
| 자동화 | GitHub Actions |
| 주가 API | Finnhub |
| BTC API | CoinGecko |
| 공시 API | SEC EDGAR (XBRL + 8-K 텍스트 파싱) |

---

## 9. 알려진 한계 및 주의사항

| 항목 | 내용 |
|------|------|
| mNAV 부채 갭 | 최신 부채는 분기 공시까지 반영 불가 (Q1 2026 = 5월 반영 예정) |
| 발행주식수 | Finnhub 수일 지연 가능 |
| BTC 보유량 | 8-K 공시 후 다음 Actions 실행 시 반영 |
| 주말/공휴일 | GitHub Actions 평일(월~금)만 실행 |
| 접근 제한 | 현재 없음 (URL 아는 누구나 접근 가능) |

---

## 10. 진행 현황

- [x] GitHub 레포 생성 및 로컬 동기화
- [x] CSV 파일 정규화 (YYYY-MM-DD, 콤마 제거, 오름차순 정렬)
- [x] Finnhub + CoinGecko API 테스트 및 연동
- [x] GitHub Actions 워크플로우 구성 (가격/보유량 분리)
- [x] HTML 대시보드 제작 (TradingView Lightweight Charts)
- [x] 정확한 역사적 mNAV 계산 (btc_holdings + mstr_shares 스텝함수)
- [x] BTC 보유량 자동 수집 (SEC EDGAR 8-K 파싱)
- [x] 발행주식수 자동 수집 (Finnhub)
- [x] 총 금융부채 자동 수집 (SEC EDGAR XBRL)
- [x] mNAV = 부채 차감 방식으로 변경 (strategy.com 기준)
- [x] UI 개선 (mNAV 카드 선두, 정규화 비교 차트, 색상 구분, 차트 동기화)
- [x] GitHub Pages 배포 (`https://jtkimpr.github.io/strategy-preferred`)
- [ ] 접근 제한 설정 (선택 사항)
