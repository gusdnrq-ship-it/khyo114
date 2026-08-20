# Pipeline Integration Notes — Technical Trading in Daily Cron

## Overview
This session integrated `technical-trading` into the **daily unified cron pipeline** (`hermes-stock-pipeline` job `abb99fffa684`).

## Integration Details

### Cron Job Configuration
- **Job ID:** `abb99fffa684` (in `hermes-stock-pipeline`)
- **Schedule:** Daily 09:30 KST (`30 9 * * *`)
- **Skills loaded:** `stock-analysis`, `technical-trading`, `hermes-stock-pipeline`
- **Model:** `google/gemini-2.5-flash-lite` via OpenRouter (pinned)

### Technical Analysis Scope (5 Tickers)
| Ticker | Code | Rationale |
|--------|------|-----------|
| 삼성전자 | 005930 | 대장주, 유동성 풍부, 벤치마크 |
| NVDA | NVDA | 해외 반도체 대장주, 변동성 큼 |
| 우리로 | 046970 | 전략 원 검증 종목 (4.5년 1회 신호, 손실 기록) |
| SKC | 011790 | 2차전지 소재, 변동성 큼 |
| TIGER K방산&우주 | 453830 | 방산/우주 테마 ETF, 추세 추종 적합 |

### Data Source Strategy (Windows/WSL)
- **Primary:** `yfinance` (pip install yfinance) — most stable, supports Korean tickers (`.KS` suffix)
- **Avoid:** `FinanceDataReader` — broken on Windows (import errors, exit -1)
- **Fallback:** Naver Finance API via curl (if yfinance fails)

### Backtest Parameters (쌍굴파기 이중 볼린저밴드)
- **Data period:** 3+ years daily (minimum for statistical validity)
- **BB1 (중기):** 20일 MA, 2σ
- **BB2 (단기):** 20일 MA, 1σ
- **Commission:** 0.015% (Korean stocks)
- **Slippage:** 0.1%
- **Position size:** Fixed 10% of capital per trade

### Output Files (Obsidian)
```
주식분석/{종목명}/
├── YYYYMMDD_{종목명}.md                    # 펀더멘털 리포트
└── YYYYMMDD_{종목명}_백테스트_쌍굴파기.md  # 기술적 분석 리포트
```
**Tags:** `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}`

### Signal Diagnosis Output
Each run produces current signal status:
- **Phase:** 1차 바닥 / 반등 중 / 2차 바닥 형성 중 / 넥라인 대기 / 돌파 확인
- **Signal:** 매수 / 매도 / 없음
- **Levels:** 진입가 / 손절가 / 목표가
- **Risk:** 높음 / 보통 / 낮음

## Key Learnings for Future Runs

### 1. Model Pinning Required
Without explicit `--model`/`--provider` in cron creation, Hermes drift detection blocks execution:
```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted...
```
**Always pin** when creating scheduled jobs.

### 2. Telegram Gateway Must Be Running
- `hermes gateway setup` → configure Telegram
- `hermes gateway install && hermes gateway start` (systemd)
- `loginctl enable-linger $USER` for WSL persistence

### 3. Windows Path & Encoding
- Use forward slashes in prompts: `C:/Users/kho/주식분석/`
- Force UTF-8: `LANG=ko_KR.UTF-8`, `PYTHONIOENCODING=utf-8`

### 4. Job Deduplication
When replacing single-analysis job with integrated pipeline:
```bash
hermes cron pause <old_job_id>  # preserve history
# keep only integrated job active
```

## Verification Commands
```bash
# Check gateway
hermes gateway status

# Check cron jobs
cronjob list  # via tool

# Test run
cronjob run <job_id>

# Verify Telegram delivery
# Check @Khyo_hermes_stock_bot within 2 min
```