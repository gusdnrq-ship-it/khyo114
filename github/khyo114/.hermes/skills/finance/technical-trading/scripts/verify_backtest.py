#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ad-hoc verification script for technical-trading backtest functions
Run this after any code changes to verify core functions work correctly.

Usage:
    python verify_backtest.py

This script tests:
1. calculate_bollinger_bands - BB calculation, NaN handling
2. detect_local_extrema - local high/low detection
3. detect_w_pattern - W-pattern detection
4. run_backtest - backtest engine (fees/slippage)
5. check_current_signal - current signal stage diagnosis
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent))
from run_daily_backtest import (
    calculate_bollinger_bands,
    detect_local_extrema,
    detect_w_pattern,
    run_backtest,
    check_current_signal
)


def create_test_data(days=100, trend='up', seed=42):
    """Create synthetic price data for testing"""
    dates = pd.date_range('2024-01-01', periods=days, freq='D')
    np.random.seed(seed)
    
    if trend == 'up':
        base = 100 + np.cumsum(np.random.randn(days) * 0.5 + 0.1)
    elif trend == 'down':
        base = 100 + np.cumsum(np.random.randn(days) * 0.5 - 0.1)
    else:
        base = 100 + np.cumsum(np.random.randn(days) * 0.5)
    
    df = pd.DataFrame({
        'Open': base * (1 + np.random.rand(days) * 0.01),
        'High': base * (1 + np.random.rand(days) * 0.02 + 0.005),
        'Low': base * (1 - np.random.rand(days) * 0.02 - 0.005),
        'Close': base,
        'Volume': np.random.randint(100000, 1000000, days)
    }, index=dates)
    
    df['High'] = df[['High', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)
    return df


def test_calculate_bollinger_bands():
    """Test BB calculation and NaN handling"""
    df = create_test_data(50)
    bb_u2, bb_m2, bb_l2 = calculate_bollinger_bands(df, 20, 2.0)
    bb_u1, bb_m1, bb_l1 = calculate_bollinger_bands(df, 20, 1.0)
    
    # Check valid indices after rolling window
    assert bb_m2.first_valid_index() is not None
    assert bb_m1.first_valid_index() is not None
    
    # Trim to valid range
    valid_start = max(bb_l2.first_valid_index(), bb_l1.first_valid_index())
    df_valid = df.loc[valid_start:]
    bb_u2 = bb_u2.loc[valid_start:]
    bb_m2 = bb_m2.loc[valid_start:]
    bb_l2 = bb_l2.loc[valid_start:]
    bb_u1 = bb_u1.loc[valid_start:]
    bb_m1 = bb_m1.loc[valid_start:]
    bb_l1 = bb_l1.loc[valid_start:]
    
    # No NaN in valid range
    assert not bb_m2.isna().any(), "NaN in BB 2σ mid"
    assert not bb_m1.isna().any(), "NaN in BB 1σ mid"
    
    # Logical consistency: upper > mid > lower
    assert (bb_u2 > bb_m2).all(), "2σ upper should be > mid"
    assert (bb_m2 > bb_l2).all(), "2σ mid should be > lower"
    assert (bb_u1 > bb_m1).all(), "1σ upper should be > mid"
    assert (bb_m1 > bb_l1).all(), "1σ mid should be > lower"
    
    # 2σ bands wider than 1σ
    assert (bb_u2 > bb_u1).all(), "2σ upper should be > 1σ upper"
    assert (bb_l2 < bb_l1).all(), "2σ lower should be < 1σ lower"
    
    print(f"✓ calculate_bollinger_bands: {len(df_valid)} valid rows, bands consistent")
    return True


def test_detect_local_extrema():
    """Test local extrema detection"""
    df = create_test_data(100)
    bb_u2, bb_m2, bb_l2 = calculate_bollinger_bands(df, 20, 2.0)
    bb_u1, bb_m1, bb_l1 = calculate_bollinger_bands(df, 20, 1.0)
    
    valid_start = max(bb_l2.first_valid_index(), bb_l1.first_valid_index())
    df_valid = df.loc[valid_start:]
    
    lows, highs = detect_local_extrema(df_valid['Close'], window=5)
    
    assert len(lows) > 0, "Should detect at least one local minimum"
    assert len(highs) > 0, "Should detect at least one local maximum"
    
    # Verify each extremum is actually local min/max
    for idx in lows:
        window = df_valid['Close'].iloc[idx-5:idx+6]
        assert df_valid['Close'].iloc[idx] == window.min(), f"Index {idx} is not local min"
    
    for idx in highs:
        window = df_valid['Close'].iloc[idx-5:idx+6]
        assert df_valid['Close'].iloc[idx] == window.max(), f"Index {idx} is not local max"
    
    print(f"✓ detect_local_extrema: {len(lows)} lows, {len(highs)} highs")
    return True


def test_detect_w_pattern():
    """Test W-pattern detection on trending data"""
    df = create_test_data(200, trend='up')
    bb_u2, bb_m2, bb_l2 = calculate_bollinger_bands(df, 20, 2.0)
    bb_u1, bb_m1, bb_l1 = calculate_bollinger_bands(df, 20, 1.0)
    
    valid_start = max(bb_l2.first_valid_index(), bb_l1.first_valid_index())
    df_valid = df.loc[valid_start:]
    bb_l2 = bb_l2.loc[valid_start:]
    bb_l1 = bb_l1.loc[valid_start:]
    bb_u1 = bb_u1.loc[valid_start:]
    
    signals = detect_w_pattern(df_valid, bb_l2, bb_l1, bb_u1)
    
    assert isinstance(signals, list)
    for sig in signals:
        assert 'first_bottom_date' in sig
        assert 'peak_date' in sig
        assert 'second_bottom_date' in sig
        assert 'breakout_date' in sig
        assert sig['second_bottom_price'] > sig['first_bottom_price'], "Higher low required"
    
    print(f"✓ detect_w_pattern: {len(signals)} signals detected")
    return True


def test_run_backtest():
    """Test backtest engine with mock signals"""
    mock_signals = [{
        'first_bottom_date': '2024-05-01', 'first_bottom_price': 90.0,
        'peak_date': '2024-05-15', 'peak_price': 110.0,
        'second_bottom_date': '2024-05-25', 'second_bottom_price': 95.0,
        'breakout_date': '2024-06-01', 'breakout_price': 111.0,
        'neckline': 110.0, 'stop_loss': 93.1, 'target_price': 125.0
    }]
    
    dates = pd.date_range('2024-05-01', periods=50, freq='D')
    prices = np.linspace(100, 120, 50)
    df = pd.DataFrame({
        'Open': prices, 'High': prices * 1.01, 'Low': prices * 0.99,
        'Close': prices, 'Volume': 1000000
    }, index=dates)
    df = df.sort_index()
    
    bb_u2, bb_m2, bb_l2 = calculate_bollinger_bands(df, 20, 2.0)
    bb_u1, bb_m1, bb_l1 = calculate_bollinger_bands(df, 20, 1.0)
    valid_start = max(bb_l2.first_valid_index(), bb_l1.first_valid_index())
    df_valid = df.loc[valid_start:]
    
    result = run_backtest(mock_signals, df_valid)
    
    assert result['total_trades'] == 1
    assert 'win_rate' in result
    assert 'avg_return_pct' in result
    assert 'total_return_pct' in result
    assert 'max_drawdown_pct' in result
    assert 'sharpe_ratio' in result
    assert 'trades' in result
    
    trade = result['trades'][0]
    assert trade['exit_reason'] in ['손절', '목표가 달성', '기간 만료']
    assert 'return_pct' in trade
    assert 'holding_days' in trade
    
    print(f"✓ run_backtest: {trade['return_pct']:.2f}% return, exit={trade['exit_reason']}")
    return True


def test_check_current_signal():
    """Test current signal stage diagnosis"""
    df = create_test_data(100)
    bb_u2, bb_m2, bb_l2 = calculate_bollinger_bands(df, 20, 2.0)
    bb_u1, bb_m1, bb_l1 = calculate_bollinger_bands(df, 20, 1.0)
    
    valid_start = max(bb_l2.first_valid_index(), bb_l1.first_valid_index())
    df_valid = df.loc[valid_start:]
    bb_u2 = bb_u2.loc[valid_start:]
    bb_m2 = bb_m2.loc[valid_start:]
    bb_l2 = bb_l2.loc[valid_start:]
    bb_u1 = bb_u1.loc[valid_start:]
    bb_m1 = bb_m1.loc[valid_start:]
    bb_l1 = bb_l1.loc[valid_start:]
    
    result = check_current_signal(df_valid, bb_l2, bb_m2, bb_u2, bb_l1, bb_m1, bb_u1)
    
    assert 'phase' in result
    assert 'phase_name' in result
    assert 'signal' in result
    assert isinstance(result['signal'], str)
    assert result['phase'] in range(7)
    assert result['signal'] in ['매수', '관찰', '없음']
    assert result['risk_level'] in ['높음', '보통', '낮음']
    assert 'current_price' in result
    assert 'current_date' in result
    
    print(f"✓ check_current_signal: {result['phase_name']}, signal={result['signal']}, risk={result['risk_level']}")
    return True


def main():
    tests = [
        ("calculate_bollinger_bands", test_calculate_bollinger_bands),
        ("detect_local_extrema", test_detect_local_extrema),
        ("detect_w_pattern", test_detect_w_pattern),
        ("run_backtest", test_run_backtest),
        ("check_current_signal", test_check_current_signal),
    ]
    
    passed = 0
    failed = []
    
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except Exception as e:
            failed.append((name, str(e)))
            print(f"✗ {name}: {e}")
    
    print(f"\n=== Results: {passed}/{len(tests)} passed ===")
    if failed:
        print("Failed tests:")
        for name, err in failed:
            print(f"  - {name}: {err}")
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()