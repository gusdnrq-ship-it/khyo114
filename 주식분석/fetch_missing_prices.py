import yfinance as yf
import pandas as pd
from pathlib import Path

data_dir = Path("/home/runner/work/khyo114/khyo114/주식분석/data")

tickers_to_fetch = {
    "046970": "046970.KS",  # 우리로
    "252670": "252670.KS",  # KODEX 200
    "453830": "453830.KS",  # TIGER K방산&우주
}

for code, yf_ticker in tickers_to_fetch.items():
    print(f"Fetching {code} ({yf_ticker})...")
    try:
        df = yf.download(yf_ticker, period="3y", interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            print(f"  No data returned for {yf_ticker}")
            continue
        
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.dropna()
        if len(df) < 60:
            print(f"  Insufficient data: {len(df)} days")
            continue
        
        # Save with expected filename
        if code == "046970":
            filename = "046970_우리로_price.csv"
        elif code == "252670":
            filename = "252670_KODEX200_price.csv"
        elif code == "453830":
            filename = "453830_TIGER_K방산우주_price.csv"
        
        df.to_csv(data_dir / filename)
        print(f"  Saved {len(df)} days to {filename}")
        
    except Exception as e:
        print(f"  Error fetching {yf_ticker}: {e}")

print("Done!")
