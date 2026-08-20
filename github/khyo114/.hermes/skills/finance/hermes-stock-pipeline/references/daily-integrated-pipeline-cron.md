# Daily Integrated Pipeline Cron Job Pattern (2026-08-20)

## Overview
Single cron job running **daily at 09:30 KST** that executes fundamental analysis (stock-analysis) + technical backtest (technical-trading) + integrated notification (hermes-stock-pipeline).

## Cron Job Configuration

### Job ID
`abb99fffa684`

### Schedule
```
30 9 * * *  # 09:30 KST daily
```

### Skills (3)
- `stock-analysis` — Fundamental analysis for 10 tickers
- `technical-trading` — W-pattern double Bollinger backtest for 5 core tickers
- `hermes-stock-pipeline` — Orchestration, Obsidian storage, Telegram delivery

### Model/Provider (Pinned)
```json
{
  "model": "nvidia/nemotron-3-ultra-550b-a55b",
  "provider": "nvidia"
}
```
**Note**: 550B model used after 70B returned 404. Monitor NVIDIA credits at build.nvidia.com.

### Delivery
`origin,telegram:6723387878`

### Target Tickers

#### Fundamental (10 tickers)
| Ticker | Name | Market | Status |
|--------|------|--------|--------|
| 005930 | 삼성전자 | KOSPI | ✅ Full data |
| 252670 | KODEX 200 | KOSPI | ⚠️ ETF - limited WiseReport |
| 453830 | TIGER K방산우주 | KOSPI | ❌ yfinance unsupported |
| 225460 | 토박스코리아 | KOSDAQ | ❌ yfinance unsupported |
| 011790 | SKC | KOSPI | ✅ Full data |
| NVDY | NVDY | US | ⚠️ Google News only |
| NVDA | 엔비디아 | US | ⚠️ Google News only |
| QQQ | QQQ | US | ⚠️ Google News only |
| SPY | SPY | US | ⚠️ Google News only |
| 047040 | 대우건설 | KOSPI | ⚠️ Extra ticker |

#### Technical Backtest (5 core)
| Ticker | Name | yfinance 30m | Backtest |
|--------|------|--------------|----------|
| 005930 | 삼성전자 | ✅ | ✅ 9 trades |
| NVDA | 엔비디아 | ✅ | ✅ 9 trades (100% win) |
| 046970 | 우리로 | ❌ 21 days only | ❌ Skipped |
| 011790 | SKC | ✅ | ✅ 3 trades |
| 453830 | TIGER K방산우주 | ❌ unsupported | ❌ Skipped |

## Execution Flow (Prompt Template)

```
통합 주식분석 파이프라인 실행 — 매일 09:30 KST

## 1단계: 펀더멘털 분석 (stock-analysis 스킬)
대상 10종목: [list above]

## 2단계: 기술적 분석 (technical-trading 스킬)
핵심 종목 5개에 대해 쌍굴파기 이중 볼린저밴드 백테스트 + 현재 시그널 진단:
[5 core tickers above]

## 3단계: 통합 알림 (Telegram)
- 펀더멘털 요약 + 기술적 요약 + Obsidian 저장 경로
- 실행 시간·소요 시간·에러 여부 포함
```

## First Run Results (2026-08-20 15:08 KST)

### Fundamental
- ✅ 10종목 분석 완료
- ⚠️ 4종목 yfinance unsupported (Korean ETFs/small caps)
- ⚠️ US tickers: Google News RSS only (no WiseReport)

### Technical Backtest
| 종목 | 거래횟수 | 승률 | 누적수익률 | 현재 시그널 |
|------|----------|------|------------|-------------|
| 삼성전자 | 9 | 55.56% | +3.76% | 1차 바닥 (관찰) |
| **NVDA** | **9** | **100%** | **+44.45%** | **🟢 돌파확인 (매수)** |
| SKC | 3 | 66.67% | -9.18% | 1차 바닥 (관찰) |
| KODEX 200 | 4 | 75% | +6.77% | 패턴 없음 |
| 우리로(046970) | - | - | - | ❌ 스킵 (21일) |

### Key Findings
1. **NVDA exceptional**: 100% win rate over 3 years with active BUY signal
2. **yfinance Korean coverage gap**: 3/5 core technical tickers unsupported
3. **Need config/watchlist.yaml**: Hardcoded tickers in prompt drift from actual targets

## Second Run (2026-08-20 15:50 KST - Manual)

### Technical Backtest Updates
| 종목 | 진입가 | 손절가 | 목표가 | R:R | 시그널 |
|------|--------|--------|--------|-----|--------|
| NVDA | $212.71 | $198.75 | $222.19 | 0.68 | 🟢 BUY 재확인 |
| 삼성전자 | - | - | - | - | Phase 1 (첫바닥) |
| SKC | - | - | - | - | Phase 1 (첫바닥) |
| KODEX 200 | - | - | - | - | NONE |
| 우리로 | - | - | - | - | SKIP |

## Critical Issues to Fix

### 1. Watchlist Config Separation
Create `config/watchlist.yaml`:
```yaml
fundamental:
  - "005930"  # 삼성전자
  - "252670"  # KODEX 200
  - "011790"  # SKC
  - "NVDA"    # 엔비디아
  - "QQQ"     # QQQ
  - "SPY"     # SPY
  - "NVDY"    # NVDY
  # Remove: 453830, 225460, 047040

technical:
  - "005930"  # 삼성전자
  - "NVDA"    # 엔비디아
  - "011790"  # SKC
  - "046970"  # 우리로 (needs KRX/Naver data source)
  - "252670"  # KODEX 200
```

### 2. Korean Data Source Fallback
For yfinance-unsupported Korean tickers:
- **Naver Finance API**: `https://api.finance.naver.com/siseJson.naver?symbol={code}&requestType=1`
- **KRX Open API**: Requires auth key
- **FinanceDataReader**: Currently broken in this environment

### 3. US Fundamental via yfinance
Add to `parse_all.py`:
```python
# yfinance Ticker objects for US
ticker = yf.Ticker("NVDA")
financials = ticker.financials      # 손익계산서
balance_sheet = ticker.balance_sheet # 대차대조표
cashflow = ticker.cashflow          # 현금흐름표
info = ticker.info                  # 시가총액, PER, PBR 등
```

### 4. Data Quality Metrics
Track per-run:
- `collection_success_rate`: tickers with full data / total tickers
- `technical_coverage`: tickers with valid backtest / technical targets
- `token_usage`: per provider/model for cost monitoring

## Cron Management Commands

### View
```bash
hermes cron list
```

### Manual Run (Today)
```bash
cronjob(action="run", job_id="abb99fffa684")
# or
hermes cron run abb99fffa684
```

### Model Pinning Update
```python
cronjob(
  action="update",
  job_id="abb99fffa684",
  model={"model": "nvidia/nemotron-3-ultra-550b-a55b", "provider": "nvidia"}
)
```

### Pause Old Single-Analysis Job
```bash
cronjob(action="pause", job_id="e70a7a1f1729")
```

## Obsidian Output Structure
```
주식분석/
├── 20260820_종합투자분석리포트.md          # 펀더멘털 통합
├── 20260820_기술적분석_요약.md             # 기술적 통합
├── 삼성전자/
│   ├── 20260820_삼성전자.md
│   └── 20260820_삼성전자_백테스트_쌍굴파기.md
├── 엔비디아/
│   ├── 20260820_엔비디아.md
│   └── 20260820_엔비디아_백테스트_쌍굴파기.md
├── SKC/
│   ├── 20260820_SKC.md
│   └── 20260820_SKC_백테스트_쌍굴파기.md
└── KODEX 200/
    ├── 20260820_KODEX 200.md
    └── 20260820_KODEX 200_백테스트_쌍굴파기.md
```

## Related Files
- `references/session-2026-08-20-integrated-pipeline.md` — First run detailed log
- `references/session-2026-08-20-second-run.md` — Second run details
- `technical-trading/references/session-2026-08-20-integrated-pipeline.md` — Technical side details
- `stock-analysis/references/session-2026-08-20-integrated-pipeline.md` — Fundamental side details