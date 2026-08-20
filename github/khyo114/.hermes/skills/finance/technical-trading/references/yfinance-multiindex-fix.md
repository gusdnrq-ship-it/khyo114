# yfinance MultiIndex Column Fix (2026-08-18)

## Problem
yfinance `download()` with `auto_adjust=True` returns a DataFrame with **MultiIndex columns** (tuple columns like `('Close', '005930.KS')`), causing:
```
'tuple' object has no attribute 'lower'
```
when trying to lowercase column names with `[c.lower() for c in df.columns]`.

## Root Cause
Default `multi_level_index=True` in yfinance v0.2.40+ creates hierarchical columns for multi-ticker downloads, but even single-ticker downloads can return MultiIndex depending on API response format.

## Fix
```python
# 1. Disable MultiIndex at download level
df = yf.download(ticker, period=period, interval=interval, 
                 progress=False, auto_adjust=True, multi_level_index=False)

# 2. Defensive column flattening (handles both cases)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [c[0].lower() if c[0] else c[1].lower() for c in df.columns]
else:
    df.columns = [c.lower() for c in df.columns]
```

## Verification
- Tested with 20 tickers (12 KR + 8 US) — all 17 working tickers returned valid DataFrames
- 3 Korean tickers failed for unrelated reasons (30m interval not supported): 046970.KS, 453830.KS, 225460.KS

## Related Files
- `scripts/technical_signal_monitor.py` — Full implementation with this fix
- `references/verification-script-pattern.md` — Ad-hoc verification template