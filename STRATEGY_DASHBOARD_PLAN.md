# Strategy Dashboard — 프로젝트 계획서

> 최초 작성: 2026-03-15
> 업데이트: 2026-03-16
> 작성 도구: claude.ai (기획 단계 대화 기반)

---

## 1. 프로젝트 개요

미국 증시에 상장된 Strategy 관련 유가증권과 BTC의 가격을 추적하고,
커스텀 지표(mNAV)를 시각적 그래프로 보여주는 웹 대시보드 구축.

- **운영 형태**: 소수 지인과 공유 (비공개 접근)
- **호스팅**: 기존 운영 중인 정적 사이트에 페이지 추가
- **개발 환경**: 여러 로컬 기기에서 작업 (GitHub로 동기화)

---

## 2. 추적 대상 유가증권

| 티커 | 종류 | 비고 |
|------|------|------|
| BTC | 암호화폐 | CoinGecko API |
| MSTR | 보통주 | Strategy 본주 |
| STRF | 우선주 | |
| STRK | 우선주 | |
| STRC | 우선주 | |
| STRD | 우선주 | 최근 상장, 데이터 불안정 가능성 있음 |

---

## 3. 커스텀 지표

### mNAV (프리미엄/NAV 비율)

```
mNAV = MSTR 시가총액 ÷ (Strategy BTC 보유량 × BTC 가격)
```

- 1.0 = BTC 순자산과 동일 가치
- 역사적 범위: 약 1.5x ~ 3.5x
- BTC 보유량은 공시 기반 수동 업데이트 (실시간 불가)

---

## 4. 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| 호스팅 | 기존 정적 사이트에 HTML 페이지 추가 | 별도 서버 불필요 |
| 백엔드 | 없음 | 브라우저에서 CSV 직접 로드 |
| 가격 데이터 | CSV 파일 (GitHub 레포 내 보관) | 브라우저가 직접 읽음 |
| 주가 API | Finnhub 또는 Alpha Vantage | 자동 업데이트용 (GitHub Actions) |
| BTC API | CoinGecko | 자동 업데이트용 (GitHub Actions) |
| 스케줄러 | GitHub Actions | 하루 2회 자동 실행 (00:00, 12:00 KST) |
| 차트 라이브러리 | TradingView Lightweight Charts 또는 Recharts | 미확정 |
| 접근 제한 | 비밀번호 페이지 또는 URL 비공개 | 미확정 |

---

## 5. 데이터 흐름

```
[자동 업데이트 — 하루 2회 (GitHub Actions)]
  CoinGecko API          → BTC 종가
  Finnhub / Alpha Vantage → MSTR, STRF, STRK, STRC, STRD 종가
       ↓
  CSV 파일에 행 추가 → GitHub 레포에 자동 커밋

[대시보드 — 브라우저]
  GitHub 레포의 CSV 파일 로드
  수동 입력 (공시 기반) → Strategy BTC 보유량
       ↓
  지표 계산 (브라우저 내 JS)  ← mNAV 계산
       ↓
  차트 렌더링
```

---

## 6. CSV 파일 구조 (예정)

| 파일명 | 컬럼 구성 | 비고 |
|--------|-----------|------|
| `btc.csv` | date, price | CoinGecko |
| `mstr.csv` | date, price | |
| `strf.csv` | date, price | |
| `strk.csv` | date, price | |
| `strc.csv` | date, price | |
| `strd.csv` | date, price | 데이터 불안정 가능성 |

- 기존 CSV는 수동으로 초기 데이터 포함
- GitHub Actions가 매일 최신 가격 행을 추가·커밋

---

## 7. 화면 구성 (초안)

- [ ] 가격 현황 카드 (BTC, MSTR, 우선주 4종)
- [ ] mNAV 시계열 차트
- [ ] BTC 가격 시계열 차트
- [ ] MSTR 가격 시계열 차트
- [ ] 우선주 가격 시계열 차트 (STRF, STRK, STRC, STRD)
- [ ] 데이터 최종 갱신 시각 표시

---

## 8. 개발 환경 설정

- **로컬 기기**: MacBook Pro 16" (macOS Tahoe), Mac Mini M4
- **코드 편집**: Claude Code CLI 활용
- **동기화**: GitHub 레포지토리
- **자동 업데이트**: GitHub Actions (기기 상태 무관하게 실행)

---

## 9. 진행 단계 (로드맵)

- [ ] **Step 1** — GitHub 레포 생성 및 이 문서 업로드
- [ ] **Step 2** — 기존 CSV 파일 정리 및 레포에 업로드 (초기 데이터 세팅)
- [ ] **Step 3** — API 선택 및 테스트 (Finnhub vs Alpha Vantage)
- [ ] **Step 4** — GitHub Actions 워크플로우 작성 (하루 2회 CSV 자동 업데이트)
- [ ] **Step 5** — 프로토타입 HTML 페이지 제작 (로컬 테스트)
- [ ] **Step 6** — 차트 라이브러리 선택 및 시각화 구현
- [ ] **Step 7** — mNAV 계산 로직 구현 (BTC 보유량 수동 입력 포함)
- [ ] **Step 8** — 기존 사이트에 페이지 통합
- [ ] **Step 9** — 접근 제한 설정
- [ ] **Step 10** — 지인 공유 테스트 및 피드백 반영

---

## 10. 미결 사항

| 항목 | 내용 |
|------|------|
| 차트 라이브러리 | TradingView Lightweight Charts vs Recharts 미확정 |
| 접근 제한 방식 | 비밀번호 vs URL 비공개 미확정 |
| STRD 데이터 | 최근 상장으로 API 지원 여부 확인 필요 |
| BTC 보유량 갱신 | 수동 입력 주기 결정 필요 |
| API 선택 | Finnhub vs Alpha Vantage 테스트 후 결정 |
| CSV 날짜 형식 | YYYY-MM-DD 통일 여부 확인 필요 |

---

*이 문서는 기획 단계 메모입니다. 개발 진행에 따라 지속 업데이트 예정.*
