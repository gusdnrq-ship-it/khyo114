#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일일 기술적 분석 백테스트 실행 스크립트 - 쌍굴파기 이중 볼린저밴드 전략
technical-trading 스킬의 메인 실행 스크립트 (cron job용)

사용법:
    python run_daily_backtest.py --data-dir "C:/Users/kho/주식분석/data" --output-dir "C:/Users/kho/주식분석"

핵심 5종목 (yfinance에서 데이터 수집 가능한 종목):
- 삼성전자(005930.KS), 엔비디아(NVDA), 우리로(046970.KS), SKC(011790.KS), KODEX 200(252670.KS)
- TIGER K방산&우주(453830.KS)는 yfinance 미지원으로 제외
"""

import pandas as pd
import numpy as np
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

def calculate_bollinger_bands(df, period=20, std_dev=2.0):
    """볼린저밴드 계산"""
    df = df.copy()
    mid = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return upper, mid, lower

def detect_local_extrema(prices, window=5):
    """로컬 극값 탐지 (최소값/최대값)"""
    local_min = []
    local_max = []
    
    for i in range(window, len(prices) - window):
        if prices.iloc[i] == prices.iloc[i-window:i+window+1].min():
            local_min.append(i)
        if prices.iloc[i] == prices.iloc[i-window:i+window+1].max():
            local_max.append(i)
    
    return local_min, local_max

def detect_w_pattern(df, bb_lower_2, bb_lower_1, bb_upper_1):
    """W-패턴(쌍바닥) 탐지"""
    signals = []
    local_min, local_max = detect_local_extrema(df['Close'], window=5)
    
    for i in range(1, len(local_min)):
        idx1 = local_min[i-1]
        idx2 = local_min[i]
        
        peaks_between = [p for p in local_max if idx1 < p < idx2]
        if not peaks_between:
            continue
        
        peak_idx = peaks_between[0]
        
        price1 = df['Close'].iloc[idx1]
        price2 = df['Close'].iloc[idx2]
        peak_price = df['Close'].iloc[peak_idx]
        
        bb1_lower_2 = bb_lower_2.iloc[idx1]
        bb2_lower_1 = bb_lower_1.iloc[idx2]
        bb_peak_upper_1 = bb_upper_1.iloc[peak_idx]
        
        cond1 = price1 <= bb1_lower_2 * 1.02
        cond2 = peak_price >= bb_peak_upper_1 * 0.98
        cond3 = price2 > price1
        cond4 = price2 <= bb2_lower_1 * 1.05
        
        if cond1 and cond2 and cond3 and cond4:
            for j in range(peak_idx + 1, min(peak_idx + 20, len(df))):
                if df['Close'].iloc[j] > peak_price:
                    signals.append({
                        'first_bottom_date': df.index[idx1].strftime('%Y-%m-%d'),
                        'first_bottom_price': round(price1, 2),
                        'peak_date': df.index[peak_idx].strftime('%Y-%m-%d'),
                        'peak_price': round(peak_price, 2),
                        'second_bottom_date': df.index[idx2].strftime('%Y-%m-%d'),
                        'second_bottom_price': round(price2, 2),
                        'breakout_date': df.index[j].strftime('%Y-%m-%d'),
                        'breakout_price': round(df['Close'].iloc[j], 2),
                        'neckline': round(peak_price, 2),
                        'stop_loss': round(price2 * 0.98, 2),
                        'target_price': round(peak_price + (peak_price - price2), 2)
                    })
                    break
    
    return signals

def run_backtest(signals, df, fee=0.00015, slippage=0.001):
    """백테스트 실행"""
    trades = []
    total_return = 0
    wins = 0
    losses = 0
    peak_equity = 1.0
    max_drawdown = 0
    
    for sig in signals:
        entry_idx = df.index.get_indexer([pd.Timestamp(sig['breakout_date'])], method='nearest')[0]
        if entry_idx >= len(df) - 1:
            continue
        
        entry_price = sig['breakout_price'] * (1 + slippage) * (1 + fee)
        stop_price = sig['stop_loss'] * (1 - slippage)
        target_price = sig['target_price'] * (1 - slippage)
        
        exit_price = None
        exit_date = None
        exit_reason = None
        holding_days = 0
        
        for k in range(entry_idx + 1, min(entry_idx + 61, len(df))):
            holding_days += 1
            high = df['High'].iloc[k]
            low = df['Low'].iloc[k]
            
            if low <= stop_price:
                exit_price = stop_price * (1 - fee)
                exit_date = df.index[k].strftime('%Y-%m-%d')
                exit_reason = '손절'
                break
            
            if high >= target_price:
                exit_price = target_price * (1 - fee)
                exit_date = df.index[k].strftime('%Y-%m-%d')
                exit_reason = '목표가 달성'
                break
        
        if exit_price is None and entry_idx + 60 < len(df):
            exit_price = df['Close'].iloc[entry_idx + 60] * (1 - fee)
            exit_date = df.index[entry_idx + 60].strftime('%Y-%m-%d')
            exit_reason = '기간 만료'
        
        if exit_price:
            ret = (exit_price - entry_price) / entry_price
            total_return += ret
            
            if ret > 0:
                wins += 1
            else:
                losses += 1
            
            peak_equity = max(peak_equity, 1 + total_return)
            current_drawdown = (peak_equity - (1 + total_return)) / peak_equity
            max_drawdown = max(max_drawdown, current_drawdown)
            
            trades.append({
                'entry_date': sig['breakout_date'],
                'entry_price': round(entry_price, 2),
                'exit_date': exit_date,
                'exit_price': round(exit_price, 2),
                'return_pct': round(ret * 100, 2),
                'holding_days': holding_days,
                'exit_reason': exit_reason,
                'stop_loss': sig['stop_loss'],
                'target_price': sig['target_price']
            })
    
    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    avg_return = (total_return / total_trades * 100) if total_trades > 0 else 0
    
    daily_returns = [t['return_pct'] / 100 / max(t['holding_days'], 1) for t in trades]
    sharpe = (np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)) if len(daily_returns) > 1 and np.std(daily_returns) > 0 else 0
    
    return {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 2),
        'avg_return_pct': round(avg_return, 2),
        'total_return_pct': round(total_return * 100, 2),
        'max_drawdown_pct': round(max_drawdown * 100, 2),
        'sharpe_ratio': round(sharpe, 2),
        'trades': trades
    }

def check_current_signal(df, bb_lower_2, bb_mid_2, bb_upper_2, bb_lower_1, bb_mid_1, bb_upper_1):
    """현재 시그널 상태 진단"""
    latest_idx = len(df) - 1
    price = df['Close'].iloc[latest_idx]
    
    recent_min, recent_max = detect_local_extrema(df['Close'].iloc[-60:], window=5)
    recent_min = [i + len(df) - 60 for i in recent_min]
    recent_max = [i + len(df) - 60 for i in recent_max]
    
    phase = 0
    first_bottom_idx = None
    peak_idx = None
    second_bottom_idx = None
    neckline = None
    entry_price = None
    stop_price = None
    target_price = None
    risk_level = "낮음"
    
    for i in range(len(recent_min) - 1):
        idx1 = recent_min[i]
        idx2 = recent_min[i+1]
        peaks_between = [p for p in recent_max if idx1 < p < idx2]
        
        if not peaks_between:
            continue
        
        pk = peaks_between[0]
        p1 = df['Close'].iloc[idx1]
        p2 = df['Close'].iloc[idx2]
        pp = df['Close'].iloc[pk]
        
        bl2_1 = bb_lower_2.iloc[idx1]
        bl1_2 = bb_lower_1.iloc[idx2]
        bu1_pk = bb_upper_1.iloc[pk]
        
        cond1 = p1 <= bl2_1 * 1.02
        cond2 = pp >= bu1_pk * 0.98
        cond3 = p2 > p1
        cond4 = p2 <= bl1_2 * 1.05
        
        if cond1 and cond2 and cond3 and cond4:
            phase = 4
            first_bottom_idx = idx1
            peak_idx = pk
            second_bottom_idx = idx2
            neckline = pp
            entry_price = round(pp * 1.001, 2)
            stop_price = round(p2 * 0.98, 2)
            target_price = round(pp + (pp - p2), 2)
            
            if price > pp:
                phase = 5
                risk_level = "높음"
            else:
                risk_level = "보통"
            break
    
    if phase == 0:
        if len(recent_min) > 0:
            last_min = recent_min[-1]
            if df['Close'].iloc[last_min] <= bb_lower_2.iloc[last_min] * 1.02:
                phase = 1
                risk_level = "보통"
    
    phase_names = {
        0: "패턴 없음",
        1: "1차 바닥 형성",
        2: "반등 중",
        3: "2차 바닥 형성 중",
        4: "넥라인 대기",
        5: "돌파 확인 (매수 시그널)",
        6: "보유 중"
    }
    
    return {
        'phase': phase,
        'phase_name': phase_names.get(phase, "알 수 없음"),
        'current_price': round(price, 2),
        'current_date': df.index[-1].strftime('%Y-%m-%d'),
        'first_bottom_date': df.index[first_bottom_idx].strftime('%Y-%m-%d') if first_bottom_idx else None,
        'first_bottom_price': round(df['Close'].iloc[first_bottom_idx], 2) if first_bottom_idx else None,
        'peak_date': df.index[peak_idx].strftime('%Y-%m-%d') if peak_idx else None,
        'peak_price': round(df['Close'].iloc[peak_idx], 2) if peak_idx else None,
        'second_bottom_date': df.index[second_bottom_idx].strftime('%Y-%m-%d') if second_bottom_idx else None,
        'second_bottom_price': round(df['Close'].iloc[second_bottom_idx], 2) if second_bottom_idx else None,
        'neckline': neckline,
        'entry_price': entry_price,
        'stop_price': stop_price,
        'target_price': target_price,
        'risk_level': risk_level,
        'signal': "매수" if phase == 5 else ("관찰" if phase in [1, 2, 3, 4] else "없음")
    }

def generate_report(ticker, name, backtest_result, current_signal, df):
    """마크다운 리포트 생성"""
    today = datetime.now().strftime("%Y%m%d")
    today_display = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    lines = []
    lines.append(f"# {name} ({ticker}) 백테스트 리포트 - 쌍굴파기 이중 볼린저밴드")
    lines.append(f"**생성일시**: {today_display}")
    lines.append(f"**데이터 기간**: {df.index[0].date()} ~ {df.index[-1].date()} ({len(df)}거래일)")
    lines.append(f"**전략**: 쌍굴파기 이중 볼린저밴드 (BB 20,2 + BB 20,1)")
    lines.append("")
    
    lines.append("## 📊 백테스트 결과 요약")
    lines.append("")
    lines.append(f"- **총 거래 횟수**: {backtest_result['total_trades']}회")
    lines.append(f"- **승률**: {backtest_result['win_rate']}% ({backtest_result['wins']}승 {backtest_result['losses']}패)")
    lines.append(f"- **평균 수익률**: {backtest_result['avg_return_pct']}%")
    lines.append(f"- **누적 수익률**: {backtest_result['total_return_pct']}%")
    lines.append(f"- **최대 낙폭(MDD)**: {backtest_result['max_drawdown_pct']}%")
    lines.append(f"- **샤프 비율**: {backtest_result['sharpe_ratio']}")
    lines.append(f"- **수수료**: 0.015% | **슬리피지**: 0.1%")
    lines.append("")
    
    if backtest_result['trades']:
        lines.append("## 📋 거래 내역 상세")
        lines.append("")
        lines.append("| 진입일 | 진입가 | 청산일 | 청산가 | 수익률 | 보유일수 | 청산사유 |")
        lines.append("|--------|--------|--------|--------|--------|----------|----------|")
        for t in backtest_result['trades']:
            lines.append(f"| {t['entry_date']} | {t['entry_price']:,} | {t['exit_date']} | {t['exit_price']:,} | {t['return_pct']}% | {t['holding_days']}일 | {t['exit_reason']} |")
        lines.append("")
    
    lines.append("## 🎯 현재 시그널 상태 진단")
    lines.append("")
    lines.append(f"- **현재 단계**: {current_signal['phase_name']} (Phase {current_signal['phase']})")
    lines.append(f"- **현재가**: {current_signal['current_price']:,} ({current_signal['current_date']})")
    lines.append(f"- **시그널**: {current_signal['signal']}")
    lines.append(f"- **리스크 레벨**: {current_signal['risk_level']}")
    lines.append("")
    
    if current_signal['phase'] >= 4:
        lines.append("### 패턴 상세")
        lines.append(f"- 1차 바닥: {current_signal['first_bottom_date']} @ {current_signal['first_bottom_price']:,}")
        lines.append(f"- 중간 고점(넥라인): {current_signal['peak_date']} @ {current_signal['peak_price']:,}")
        lines.append(f"- 2차 바닥: {current_signal['second_bottom_date']} @ {current_signal['second_bottom_price']:,}")
        lines.append("")
        lines.append("### 매매 계획")
        lines.append(f"- **진입가**: {current_signal['entry_price']:,}")
        lines.append(f"- **손절가**: {current_signal['stop_price']:,}")
        lines.append(f"- **목표가**: {current_signal['target_price']:,}")
        if current_signal['entry_price'] and current_signal['stop_price']:
            rr = (current_signal['target_price'] - current_signal['entry_price']) / (current_signal['entry_price'] - current_signal['stop_price'])
            lines.append(f"- **위험보상비(R:R)**: {rr:.2f}")
        lines.append("")
    
    lines.append("## ⚠️ 유의사항")
    lines.append("- 본 백테스트는 과거 데이터 기반으로 미래 수익을 보장하지 않습니다.")
    lines.append("- 수수료 0.015%, 슬리피지 0.1% 반영, 세금(0.23%) 미반영")
    lines.append("- 표본 수 부족 시 통계적 유의성 낮음 (과적합 위험)")
    lines.append("- 실전은 호가창 유동성, 갭 리스크 등으로 성과가 더 낮을 수 있음")
    lines.append("- 투자 결정은 본인 판단과 책임 하에 이루어져야 합니다.")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='일일 기술적 분석 백테스트 실행')
    parser.add_argument('--data-dir', required=True, help='가격 데이터 CSV 디렉토리')
    parser.add_argument('--output-dir', required=True, help='리포트 저장 디렉토리')
    args = parser.parse_args()
    
    tickers = {
        "005930": {"name": "삼성전자", "file": "005930_삼성전자_price.csv"},
        "NVDA": {"name": "엔비디아", "file": "NVDA_엔비디아_price.csv"},
        "046970": {"name": "우리로", "file": "046970_우리로_price.csv"},
        "011790": {"name": "SKC", "file": "011790_SKC_price.csv"},
        "252670": {"name": "KODEX 200", "file": "252670_KODEX200_price.csv"},
    }
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    all_results = {}
    
    for ticker, info in tickers.items():
        print(f"\n=== {info['name']} ({ticker}) 분석 중... ===")
        
        file_path = data_dir / info['file']
        if not file_path.exists():
            print(f"  파일 없음: {file_path}")
            continue
        
        try:
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            df = df.sort_index()
            
            df = df.dropna()
            
            if len(df) < 60:
                print(f"  데이터 부족: {len(df)}일 (최소 60일 필요)")
                continue
            
            bb_upper_2, bb_mid_2, bb_lower_2 = calculate_bollinger_bands(df, 20, 2.0)
            bb_upper_1, bb_mid_1, bb_lower_1 = calculate_bollinger_bands(df, 20, 1.0)
            
            valid_start = max(bb_lower_2.first_valid_index(), bb_lower_1.first_valid_index())
            if valid_start is not None:
                df = df.loc[valid_start:]
                bb_upper_2 = bb_upper_2.loc[valid_start:]
                bb_mid_2 = bb_mid_2.loc[valid_start:]
                bb_lower_2 = bb_lower_2.loc[valid_start:]
                bb_upper_1 = bb_upper_1.loc[valid_start:]
                bb_mid_1 = bb_mid_1.loc[valid_start:]
                bb_lower_1 = bb_lower_1.loc[valid_start:]
            
            signals = detect_w_pattern(df, bb_lower_2, bb_lower_1, bb_upper_1)
            print(f"  탐지된 패턴: {len(signals)}개")
            
            backtest_result = run_backtest(signals, df)
            
            current_signal = check_current_signal(df, bb_lower_2, bb_mid_2, bb_upper_2, bb_lower_1, bb_mid_1, bb_upper_1)
            
            report = generate_report(ticker, info['name'], backtest_result, current_signal, df)
            
            stock_dir = output_dir / info['name']
            stock_dir.mkdir(exist_ok=True)
            today = datetime.now().strftime("%Y%m%d")
            report_path = stock_dir / f"{today}_{info['name']}_백테스트_쌍굴파기.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"  리포트 저장: {report_path}")
            
            all_results[ticker] = {
                'name': info['name'],
                'backtest': backtest_result,
                'current_signal': current_signal,
                'report_path': str(report_path)
            }
            
        except Exception as e:
            print(f"  에러 발생: {e}")
            import traceback
            traceback.print_exc()
    
    generate_summary_report(all_results, output_dir)
    
    return all_results

def generate_summary_report(all_results, output_dir):
    """통합 요약 리포트 생성"""
    today = datetime.now().strftime("%Y%m%d")
    today_display = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    lines = []
    lines.append("# 일일 기술적 분석 요약 리포트 - 쌍굴파기 이중 볼린저밴드")
    lines.append(f"**생성일시**: {today_display}")
    lines.append(f"**대상 종목**: {len(all_results)}개")
    lines.append(f"**전략**: 쌍굴파기 이중 볼린저밴드 (BB 20일, 2σ + BB 20일, 1σ)")
    lines.append("")
    
    lines.append("## 📊 종목별 백테스트 요약")
    lines.append("")
    lines.append("| 종목 | 거래횟수 | 승률 | 평균수익률 | 누적수익률 | MDD | 샤프 |")
    lines.append("|------|----------|------|------------|------------|-----|------|")
    for ticker, res in all_results.items():
        bt = res['backtest']
        lines.append(f"| {res['name']} ({ticker}) | {bt['total_trades']} | {bt['win_rate']}% | {bt['avg_return_pct']}% | {bt['total_return_pct']}% | {bt['max_drawdown_pct']}% | {bt['sharpe_ratio']} |")
    lines.append("")
    
    lines.append("## 🎯 현재 시그널 현황")
    lines.append("")
    lines.append("| 종목 | 현재단계 | 시그널 | 현재가 | 진입가 | 손절가 | 목표가 | 리스크 |")
    lines.append("|------|----------|--------|--------|--------|--------|--------|--------|")
    for ticker, res in all_results.items():
        cs = res['current_signal']
        entry = f"{cs['entry_price']:,}" if cs['entry_price'] else "-"
        stop = f"{cs['stop_price']:,}" if cs['stop_price'] else "-"
        target = f"{cs['target_price']:,}" if cs['target_price'] else "-"
        lines.append(f"| {res['name']} ({ticker}) | {cs['phase_name']} | {cs['signal']} | {cs['current_price']:,} | {entry} | {stop} | {target} | {cs['risk_level']} |")
    lines.append("")
    
    lines.append("## 💾 개별 리포트 저장 위치")
    lines.append("")
    for ticker, res in all_results.items():
        lines.append(f"- {res['name']}: `{res['report_path']}`")
    lines.append("")
    
    lines.append("---")
    lines.append("*자동 생성된 리포트입니다. 투자 참고용으로만 활용하세요.*")
    
    summary_path = output_dir / f"{today}_기술적분석_요약.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"\n통합 요약 리포트 저장: {summary_path}")

if __name__ == '__main__':
    main()