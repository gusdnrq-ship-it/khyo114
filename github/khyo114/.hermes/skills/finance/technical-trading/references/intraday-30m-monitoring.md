# Intraday 30-Minute Signal Monitoring Pattern (2026-08-18)

## Context
Cron job requirement: Monitor 20 tickers every 30 minutes during market hours (09:30-15:30 KST) for W-Pattern Double Bollinger Band signals.

## Architecture: Local-First, LLM-Minimal

```
┌─────────────────────────────────────────────────────────────┐
│  LOCAL PYTHON (100% data fetch, indicators, pattern detect) │
├─────────────────────────────────────────────────────────────┤
│  1. fetch_price_data()  — yfinance 30m, 60d lookback       │
│  2. calculate_indicators() — BB(20,2) + BB(20,1) + local   │
│     extrema (window=5)                                      │
│  3. detect_w_pattern_phase() — 6-phase state machine       │
│  4. generate_signal() — BUY/SELL/HOLD mapping              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (only when signal ≠ HOLD)
┌─────────────────────────────────────────────────────────────┐
│  LLM CALL (minimal tokens, ~200/ticker)                     │
├─────────────────────────────────────────────────────────────┤
│  Prompt template → 3-line Korean Telegram summary with 🔔  │
└─────────────────────────────────────────────────────────────┘
```

## Phase State Machine (6 Phases)

| Phase | Description | Signal |
|-------|-------------|--------|
| 0 | 패턴 없음 | HOLD |
| 1 | 1차 바닥 형성/가능성 (하단밴드 2σ 터치/근접) | HOLD |
| 2 | 중간 반등 완료 (상단밴드 1σ 도달), 2차 바닥 대기 | HOLD |
| 3 | 2차 바닥 형성 중, Higher Low 확인됨 | HOLD |
| 4 | 넥라인 돌파 대기 (이미 돌파됨, 진입가 확정) | HOLD |
| **5** | **넥라인 돌파 확인 (종가 기준) → 매수** | **BUY** |
| **6** | **손절/트레일링 익절** | **SELL** |

## Key Implementation Details

### Local Extrema Detection
```python
df['local_min'] = df['low'].rolling(5, center=True).min() == df['low']
df['local_max'] = df['high'].rolling(5, center=True).max() == df['high']
```
- `center=True` ensures symmetric window around each point
- Avoids lookahead bias in backtest but acceptable for real-time monitoring

### Higher Low Validation
```python
# 2차 바닥가 > 1차 바닥가
if second_bottom_price > first_bottom_price:
    details['higher_low'] = True
```
Critical for W-pattern validity — filters false double bottoms.

### Neckline Breakout Confirmation
```python
# Current close > neckline AND previous close <= neckline
if last['close'] > neckline and prev['close'] <= neckline:
    phase = 5  # Confirmed breakout
```
Uses prior-bar confirmation to avoid intrabar false breaks.

### Trailing Exit (Phase 6)
```python
# Stop loss: 2차 바닥 이탈
if last['close'] < details['stop_loss']:
    phase = 6
# Trailing: 1σ band breakdown
elif last['close'] < last['bb20_1_lower']:
    phase = 6
```

## Deduplication Logic
- Track last signal timestamp per ticker
- Suppress same-signal re-alerts within 1 hour (3600s)

## Korean Ticker 30m Limitations (yfinance)
| Ticker | Issue | Workaround |
|--------|-------|------------|
| 046970.KS (우리로) | KeyError tradingPeriods | Use daily + manual 30m approx |
| 453830.KS (TIGER K방산) | 404 Not Found | Use daily or alternative source |
| 225460.KS (토박스코리아) | 404 Not Found | Use daily or alternative source |

**Recommendation**: For small-cap/ETF Korean tickers, fall back to daily timeframe with adjusted BB periods (20-day → ~20*13 = 260 30m bars equivalent).

## Telegram Alert Format
```
🔔 [기술적 시그널] 삼성전자(005930) - 매수 신호
현재가: 78,500원 | 단계: 넥라인 돌파 확인(단계5)
진입: 78,300 | 손절: 74,200 | 목표: 84,800
리스크: MEDIUM | 30분봉 BB(20,2)+BB(20,1)
[상세: 주식분석/삼성전자/20260818_삼성전자_기술적.md]
```

## Obsidian Storage
```
주식분석/{종목명}/{YYYYMMDD}_{종목명}_기술적.md
Tags: #기술적분석 #볼린저밴드 #쌍굴파기 #시그널 #{종목코드}
```

## Files
- `scripts/technical_signal_monitor.py` — Complete standalone monitor
- `references/verification-script-pattern.md` — Verification template
- `references/windows-python-env.md` — Critical: must use Hermes venv Python (not system Python 3.14)
- `references/session-2026-08-19-intraday-monitoring.md` — This session execution log