# Intraday Technical Signal Monitoring Cron Job (2026-08-18)

## Purpose
Separate cron job for **intraday 30-minute monitoring** (09:30-15:30 KST, weekdays) — distinct from daily 09:30 fundamental pipeline.

## Cron Schedule
```
# Every 30 minutes during market hours (Mon-Fri 09:30-15:30 KST)
# 30 9-15 * * 1-5  →  09:30, 10:00, 10:30, ..., 15:00, 15:30
```

## Hermes Cron Create Command
```bash
hermes cron create "30 9-15 * * 1-5" \
  "장중 30분마다 기술적 시그널 감시 (쌍굴파기 이중 볼린저밴드)

## 대상 20종목
- 국내 12: 삼성전자(005930), SK하이닉스(000660), SKC(011790), 우리로(046970), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), LG에너지솔루션(373220), 삼성SDI(006400), NAVER(035420), 카카오(035720), 현대차(005380)
- 해외 8: NVDA, NVDY, QQQ, TQQQ, AAPL, MSFT, GOOGL, AMZN

## 실행 로직
1. yfinance 30분봉 수집 (최근 60일)
2. BB(20,2)+BB(20,1) 계산 + 로컬 극값 탐지
3. W-패턴 6단계 상태 머신으로 현재 단계 진단
4. Phase 5(매수) / Phase 6(매도) 발생 시에만 LLM 호출 → Telegram 3줄 요약
5. 시그널 발생 종목만 Obsidian 저장

## 모델 고정
- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b" \
  --skill technical-trading \
  --name "장중 기술적 시그널 실시간 감시 (30분 주기)" \
  --model nvidia/nemotron-3-ultra-550b-a55b \
  --provider nvidia \
  --deliver origin,telegram:6723387878
```

## Key Differences from Daily Pipeline

| Aspect | Daily Pipeline (09:30) | Intraday Monitor (30min) |
|--------|------------------------|--------------------------|
| **Trigger** | `30 9 * * *` | `30 9-15 * * 1-5` |
| **Focus** | Fundamental + Technical backtest | Real-time signal detection |
| **Timeframe** | Daily bars (3yr lookback) | 30-min bars (60d lookback) |
| **LLM Usage** | Full reports for all 10 tickers | Minimal — only signal tickers |
| **Output** | Obsidian reports for all | Alerts + Obsidian for signals only |
| **Model** | google/gemini-2.5-flash-lite (OpenRouter) | nvidia/nemotron-3-ultra (NVIDIA) |

## Deduplication with Daily Pipeline
- Daily pipeline runs **once at 09:30** — includes technical backtest + current signal
- Intraday monitor runs **every 30min** — only checks for NEW signals since last run
- Both write to Obsidian but different files:
  - Daily: `{YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md`
  - Intraday: `{YYYYMMDD}_{종목명}_기술적.md`

## Execution Environment Critical Note
**Python Environment**: The intraday monitor script (`technical_signal_monitor.py`) uses yfinance, pandas, numpy which require the Hermes venv Python. The system Python 3.14 (Windows Store) fails with numpy C-extension error:
```
ModuleNotFoundError: No module named 'numpy.core._multiarray_umath'
```

**Fix**: Cron job command MUST use full venv Python path:
```bash
/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe /path/to/technical_signal_monitor.py
```

See `references/windows-python-env.md` in technical-trading skill for details.

## Model Pinning Critical
**Must specify `--model` and `--provider` explicitly** to prevent drift errors:
```bash
--model nvidia/nemotron-3-ultra-550b-a55b --provider nvidia
```
Without this, cron job fails with "global inference config drifted" when default model changes.

## Gateway Dependency
Telegram delivery requires running gateway:
```bash
hermes gateway install && hermes gateway start
```
Verify: `hermes gateway status` → "Gateway is running"

## Error Handling
- Individual ticker failures don't stop batch (try/except per ticker)
- yfinance 30m unsupported tickers (046970.KS, 453830.KS, 225460.KS) skipped with log
- Signal deduplication: same ticker + same signal suppressed for 1 hour

## Files
- `scripts/technical_signal_monitor.py` — Complete monitor implementation
- `references/intraday-30m-monitoring.md` — Detailed pattern documentation (in technical-trading skill)
- `references/windows-python-env.md` — Critical: must use Hermes venv Python (not system Python 3.14)
- `references/session-2026-08-19-intraday-monitoring.md` — 2026-08-19 execution log (in technical-trading skill)