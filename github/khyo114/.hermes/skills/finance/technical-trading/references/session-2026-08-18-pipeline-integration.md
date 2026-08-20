# Session 2026-08-18 — Technical Trading Pipeline Integration

## Integration with hermes-stock-pipeline Cron Job

### Cron Job: `abb99fffa684` (Integrated Pipeline)
- **Schedule**: `30 9 * * *` (09:30 KST daily)
- **Skills**: `stock-analysis,technical-trading,hermes-stock-pipeline`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`)

### Technical Trading Targets (5 Core Tickers)
| Ticker | Name | Market | Priority |
|--------|------|--------|----------|
| 005930 | 삼성전자 | KOSPI | Core holding (20.5%) |
| NVDA | 엔비디아 | NASDAQ | Profitable holding |
| 046970 | 우리로 | KOSPI | Previous backtest validation |
| 011790 | SKC | KOSPI | Semiconductor materials |
| 453830 | TIGER K방산&우주 | KOSPI | Defense/space ETF |

### Daily Execution Flow (Technical Part)

1. **Data Fetch** (yfinance)
   - Period: 3 years daily OHLCV
   - Tickers: `005930.KS`, `NVDA`, `046970.KS`, `011790.KS`, `453830.KS`

2. **Indicator Calculation**
   - BB 20,2: 20-day SMA ± 2σ (medium-term)
   - BB 20,1: 20-day SMA ± 1σ (short-term)

3. **W-Pattern Detection**
   - 1st bottom: touch/breach BB 20,2 lower → rebound
   - Rebound: reach BB 20,1 upper
   - 2nd bottom: support near BB 20,1 lower, higher low than 1st
   - Neckline break: close above intermediate high → BUY signal

4. **Backtest** (each ticker independently)
   - Fee: 0.015% (KR) / 0% (US, approximate)
   - Slippage: 0.1%
   - Position: fixed 10% per trade
   - Metrics: win rate, avg return, MDD, Sharpe, trade count

5. **Current Signal Diagnosis** (latest 60 days)
   - Pattern stage: 1st bottom / rebound / 2nd forming / neckline wait / breakout confirmed
   - Signal: BUY / SELL / NONE
   - Levels: entry, stop-loss, target
   - Risk: High / Medium / Low

6. **Output Files**
   ```
   주식분석/{종목명}/{YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md
   ```
   Tags: `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}`

7. **Telegram Summary** (per ticker)
   ```
   📈 [기술적] 삼성전자 (005930)
   단계: 2차 바닥 형성 중
   시그널: 없음 (대기)
   진입가: 78,500 | 손절: 72,300 | 목표: 89,200
   리스크: 보통
   백테스트: 4.5년 3회 거래, 승률 66%, MDD -8.2%
   ```

## Previous Validation (2026-07-03)
- **Test ticker**: 우리로(046970)
- **Period**: 4.5 years
- **Signals**: 1 occurrence
- **Result**: Loss
- **Conclusion**: Sample size too small for statistical significance — continue monitoring

## yfinance Limitations for Korean Market
- ETFs (KODEX 200, TIGER K방산&우주): may have limited history or adjusted close issues
- Small caps (토박스코리아): occasional missing data
- **Workaround**: Use `period="max"` and validate row count; fallback to Naver Finance API if critical

## Model Configuration
- Primary: NVIDIA NIM `nvidia/nemotron-3-ultra-550b-a55b` (verified working 2026-08-18)
- Fallback: Google Gemini `gemini-2.5-flash` (quota limited)
- All cron jobs pinned explicitly via `cronjob` tool

## Gateway Dependency
- Telegram delivery requires `hermes gateway` running
- WSL: Use `hermes gateway install && hermes gateway start` (Windows Startup folder)
- Verify: `hermes gateway status` → PID running

## Next Verification (2026-08-19)
- [ ] 09:30 cron fires automatically
- [ ] 5 tickers processed without yfinance errors
- [ ] Backtest + signal diagnosis completes
- [ ] Obsidian files created with correct tags
- [ ] Telegram summary received