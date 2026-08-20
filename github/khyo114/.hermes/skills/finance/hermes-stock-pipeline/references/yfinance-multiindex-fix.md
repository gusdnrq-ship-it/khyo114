# yfinance MultiIndex Column Fix for Pipeline (2026-08-18)

## Problem
yfinance `download()` with `auto_adjust=True` returns DataFrame with **MultiIndex columns** (tuples like `('Close', '005930.KS')`), breaking column normalization:
```
'tuple' object has no attribute 'lower'
```

## Root Cause
Default `multi_level_index=True` in yfinance v0.2.40+ creates hierarchical columns even for single-ticker downloads depending on API response format.

## Fix for Pipeline Scripts
Apply to any script using `yf.download()` for Korean/US tickers:

```python
# 1. Disable MultiIndex at download level
df = yf.download(ticker, period=period, interval=interval, 
                 progress=False, auto_adjust=True, multi_level_index=False)

# 2. Defensive column flattening (handles both MultiIndex and flat)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [c[0].lower() if c[0] else c[1].lower() for c in df.columns]
else:
    df.columns = [c.lower() for c in df.columns]
```

## Affected Pipeline Components
- `technical-trading` skill: `fetch_price_data()` in `scripts/technical_signal_monitor.py`
- `stock-analysis` skill: Any `parse_all.py` or data fetchers using yfinance
- Daily pipeline backtest data collection
- Intraday 30m monitoring data collection

## Verification
Tested with 20 tickers (12 KR + 8 US):
- ✅ 17 tickers: Normal DataFrame with flat columns after fix
- ❌ 3 KR tickers: 30m interval unsupported (unrelated to MultiIndex)
  - 046970.KS (우리로) — KeyError tradingPeriods
  - 453830.KS (TIGER K방산&우주) — 404 Not Found
  - 225460.KS (토박스코리아) — 404 Not Found

## Recommendation
Add this fix to ALL yfinance download calls in pipeline skills to prevent silent failures when yfinance updates its API response format.

## Related
- `technical-trading/references/yfinance-multiindex-fix.md` — Original documentation
- `technical-trading/references/yfinance-limitations.md` — Known Korean ticker limitations