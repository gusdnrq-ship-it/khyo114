# Integrated Pipeline Cron Setup — Session Notes

## Overview
This session created a **unified daily cron job** that runs both:
1. `stock-analysis` — fundamental analysis for 10 tickers
2. `technical-trading` — backtest + signal check for 5 core tickers using 쌍굴파기 이중 볼린저밴드

## Cron Job Configuration

**Job ID:** `abb99fffa684`
**Schedule:** `30 9 * * *` (daily 09:30 KST)
**Skills:** `stock-analysis`, `technical-trading`, `hermes-stock-pipeline`
**Model:** `google/gemini-2.5-flash-lite` via OpenRouter (pinned to prevent drift)
**Delivery:** `origin,telegram:6723387878`

## Key Integration Points

### 1. Ticker Split Strategy
| Analysis Type | Tickers (5-6 each) |
|---------------|-------------------|
| Fundamental (10) | 삼성전자(005930), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), SKC(011790), NVDY, NVDA, QQQ + 2 more |
| Technical (5) | 삼성전자(005930), NVDA, 우리로(046970), SKC(011790), TIGER K방산&우주(453830) |

**Rationale:** Technical backtesting needs 3+ years of daily data; fundamental covers full portfolio.

### 2. Duplicate Prevention
- Original single-analysis job `e70a7a1f1729` **paused** (not deleted) to preserve history
- Only integrated pipeline runs at 09:30

### 3. Telegram Gateway Setup (Critical Path)
```bash
# One-time setup
hermes gateway setup
# → Select Telegram → Manual token entry (QR flow timed out)
# → Allowlist: 6723387878
# → Home channel: 6723387878
hermes gateway install && hermes gateway start
# → systemd service enabled, linger active
```

**Gotcha:** QR code onboarding timed out; manual token entry worked. Document this fallback.

### 4. Model Pinning (Drift Prevention)
Job explicitly sets:
```yaml
model: "google/gemini-2.5-flash-lite"
provider: "openrouter"
```
Without pinning, Hermes drift detection blocks execution with:
> `RuntimeError: Skipped to prevent unintended spend: global inference config drifted...`

### 5. Windows/WSL Path Handling
- Use forward slashes in prompts: `C:/Users/kho/주식분석/`
- yfinance for price data (FinanceDataReader broken on Windows)
- Encoding: `LANG=ko_KR.UTF-8`, `PYTHONIOENCODING=utf-8`

## Verification Checklist
- [ ] `hermes gateway status` → active (running)
- [ ] `cronjob list` → integrated job enabled, paused job disabled
- [ ] Test run (`cronjob run <id>`) → `execution_success: true`
- [ ] Telegram bot receives message within 1-2 min of run

## Troubleshooting Log
| Issue | Resolution |
|-------|------------|
| `hermes cron run` CLI says "not found" | Use tool `cronjob(action='run', job_id=...)` instead |
| Telegram delivery error: "platform not configured" | Run `hermes gateway setup` → configure Telegram |
| Model drift error on scheduled run | Pin model/provider in cron job creation |
| yfinance ModuleNotFoundError | `pip install yfinance` in Hermes venv |
| WSL systemd service dies on logout | `loginctl enable-linger $USER` (already done) |