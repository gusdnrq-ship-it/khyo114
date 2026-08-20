#!/usr/bin/env python3
"""
Intraday Technical Signal Monitor - 쌍굴파기 이중 볼린저밴드 30분봉 실시간 감시
평일 09:30~15:30 KST, 30분 주기 실행
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import yfinance as yf
import pandas as pd
import numpy as np


# ==================== 설정 ====================

# KST 타임존
KST = timezone(timedelta(hours=9))

# 대상 20종목 (yfinance 30분봉 지원 종목만)
TICKERS = {
    # 국내 9개 (대형주 + KODEX 200만 yfinance intraday 지원)
    "005930": {"name": "삼성전자", "yf": "005930.KS", "market": "KR"},
    "000660": {"name": "SK하이닉스", "yf": "000660.KS", "market": "KR"},
    "011790": {"name": "SKC", "yf": "011790.KS", "market": "KR"},
    "252670": {"name": "KODEX 200", "yf": "252670.KS", "market": "KR"},
    "373220": {"name": "LG에너지솔루션", "yf": "373220.KS", "market": "KR"},
    "006400": {"name": "삼성SDI", "yf": "006400.KS", "market": "KR"},
    "035420": {"name": "NAVER", "yf": "035420.KS", "market": "KR"},
    "035720": {"name": "카카오", "yf": "035720.KS", "market": "KR"},
    "005380": {"name": "현대차", "yf": "005380.KS", "market": "KR"},
    # 해외 8개
    "NVDA": {"name": "NVDA", "yf": "NVDA", "market": "US"},
    "NVDY": {"name": "NVDY", "yf": "NVDY", "market": "US"},
    "QQQ": {"name": "QQQ", "yf": "QQQ", "market": "US"},
    "TQQQ": {"name": "TQQQ", "yf": "TQQQ", "market": "US"},
    "AAPL": {"name": "AAPL", "yf": "AAPL", "market": "US"},
    "MSFT": {"name": "MSFT", "yf": "MSFT", "market": "US"},
    "GOOGL": {"name": "GOOGL", "yf": "GOOGL", "market": "US"},
    "AMZN": {"name": "AMZN", "yf": "AMZN", "market": "US"},
}

# 제외된 종목 (yfinance intraday 미지원)
# "046970": 우리로 - 소형주, intraday 미제공
# "453830": TIGER K방산&우주 - ETF, yfinance 미지원
# "225460": 토박스코리아 - 소형주, intraday 미제공

# 볼린저밴드 파라미터
BB_PERIOD = 20
BB_STD_LONG = 2.0   # 중기
BB_STD_SHORT = 1.0  # 단기

# 극값 탐지 윈도우
EXTREMA_WINDOW = 5

# Obsidian 저장 경로
OBSIDIAN_BASE = Path(r"C:/Users/kho/주식분석")

# 시그널 중복 방지 (메모리상, 실제로는 파일로 영속화 권장)
SIGNAL_COOLDOWN_MINUTES = 60


class Phase(Enum):
    """W-패턴 단계"""
    NONE = 0          # 패턴 없음
    FIRST_BOTTOM = 1  # 1차 바닥 형성
    REBOUND = 2       # 중간 반등 (상단 1σ 이상)
    SECOND_BOTTOM = 3 # 2차 바닥 형성 중
    NECKLINE_WAIT = 4 # 넥라인 대기
    BREAKOUT = 5      # 돌파 확인 → 매수 시그널
    HOLDING = 6       # 보유 중 (손절/익절 모니터링)


class SignalType(Enum):
    NONE = "none"
    BUY = "buy"
    SELL_STOP = "sell_stop"
    SELL_TRAIL = "sell_trail"


@dataclass
class SignalState:
    """종목별 시그널 상태"""
    code: str
    name: str
    phase: Phase
    signal: SignalType
    current_price: float
    entry_price: Optional[float]
    stop_price: Optional[float]
    target_price: Optional[float]
    risk_level: str  # HIGH/MEDIUM/LOW
    first_bottom_price: Optional[float]
    first_bottom_date: Optional[str]
    neckline_price: Optional[float]
    second_bottom_price: Optional[float]
    second_bottom_date: Optional[str]
    last_signal_time: Optional[str]  # 중복 방지용


# ==================== 유틸리티 함수 ====================

def get_kst_now() -> datetime:
    return datetime.now(KST)


def is_market_hours() -> bool:
    """장중 시간 확인 (09:30~15:30 KST, 평일)"""
    now = get_kst_now()
    if now.weekday() >= 5:  # 주말
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def fetch_intraday_data(ticker_yf: str, days: int = 30) -> Optional[pd.DataFrame]:
    """yfinance로 30분봉 데이터 수집 (period 파라미터 사용, 한국 종목 30일 제한)"""
    try:
        # period 파라미터 사용 (start/end보다 intraday에 안정적)
        period = f"{days}d"
        df = yf.download(
            ticker_yf,
            period=period,
            interval="30m",
            progress=False,
            auto_adjust=True,
            prepost=False,
            threads=False
        )
        if df is None or df.empty:
            return None
        
        # MultiIndex 컬럼 처리 (yfinance 1.6+)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.reset_index()
        # 컬럼명 표준화: Datetime -> date, 나머지는 소문자
        rename_map = {}
        for c in df.columns:
            if c.lower() == 'datetime':
                rename_map[c] = 'date'
            else:
                rename_map[c] = c.lower()
        df = df.rename(columns=rename_map)
        
        # 필수 컬럼 확인
        required = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(c in df.columns for c in required):
            print(f"  컬럼 부족: {df.columns.tolist()}")
            return None
        
        df = df[required].copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[ERROR] {ticker_yf} 데이터 수집 실패: {e}")
        return None


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """볼린저밴드 계산"""
    df = df.copy()
    df['bb_mid'] = df['close'].rolling(window=period).mean()
    df['bb_std'] = df['close'].rolling(window=period).std()
    df['bb_upper'] = df['bb_mid'] + std_dev * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - std_dev * df['bb_std']
    return df


def find_local_extrema(series: pd.Series, window: int = 5) -> Tuple[List[int], List[int]]:
    """로컬 최저점/최고점 인덱스 탐지"""
    lows = []
    highs = []
    for i in range(window, len(series) - window):
        if series.iloc[i] == series.iloc[i-window:i+window+1].min():
            lows.append(i)
        if series.iloc[i] == series.iloc[i-window:i+window+1].max():
            highs.append(i)
    return lows, highs


def detect_w_pattern_phase(df: pd.DataFrame) -> Dict[str, Any]:
    """
    W-패턴 단계 진단 (상태 머신)
    반환: {phase, first_bottom_idx, first_bottom_price, first_bottom_date,
          neckline_idx, neckline_price, second_bottom_idx, second_bottom_price, second_bottom_date}
    """
    # 지표 계산
    df = calculate_bollinger_bands(df, BB_PERIOD, BB_STD_LONG)
    df['bb_mid_1'] = df['close'].rolling(BB_PERIOD).mean()
    df['bb_std_1'] = df['close'].rolling(BB_PERIOD).std()
    df['bb_upper_1'] = df['bb_mid_1'] + BB_STD_SHORT * df['bb_std_1']
    df['bb_lower_1'] = df['bb_mid_1'] - BB_STD_SHORT * df['bb_std_1']
    
    # 로컬 극값 탐지
    lows, highs = find_local_extrema(df['low'], EXTREMA_WINDOW)
    _, highs_close = find_local_extrema(df['high'], EXTREMA_WINDOW)
    
    if len(lows) < 2 or len(highs_close) < 1:
        return {"phase": Phase.NONE}
    
    # 가장 최근 두 개의 저점과 그 사이의 고점 찾기
    # 뒤에서부터 탐색
    last_low_idx = lows[-1]
    prev_lows = [l for l in lows if l < last_low_idx]
    if not prev_lows:
        return {"phase": Phase.NONE}
    
    first_low_idx = prev_lows[-1]
    
    # 첫 저점과 마지막 저점 사이의 고점(넥라인 후보)
    neckline_candidates = [h for h in highs_close if first_low_idx < h < last_low_idx]
    if not neckline_candidates:
        return {"phase": Phase.NONE}
    
    neckline_idx = max(neckline_candidates, key=lambda h: df['high'].iloc[h])
    
    first_low_price = df['low'].iloc[first_low_idx]
    first_low_date = df['date'].iloc[first_low_idx].strftime("%Y-%m-%d %H:%M")
    neckline_price = df['high'].iloc[neckline_idx]
    last_low_price = df['low'].iloc[last_low_idx]
    last_low_date = df['date'].iloc[last_low_idx].strftime("%Y-%m-%d %H:%M")
    
    # 현재가 및 밴드 값
    current_price = df['close'].iloc[-1]
    bb_lower_2 = df['bb_lower'].iloc[-1]
    bb_upper_1 = df['bb_upper_1'].iloc[-1]
    bb_lower_1 = df['bb_lower_1'].iloc[-1]
    
    # === 단계 판단 로직 ===
    
    # 1차 바닥 조건: 첫 저점이 하단 2σ 터치/이탈 후 반등
    first_touched_2sigma = first_low_price <= df['bb_lower'].iloc[first_low_idx] * 1.001
    first_rebounded = df['close'].iloc[first_low_idx:neckline_idx].max() > df['bb_mid'].iloc[first_low_idx]
    
    if not (first_touched_2sigma and first_rebounded):
        return {"phase": Phase.NONE}
    
    # 중간 반등 조건: 넥라인이 상단 1σ 이상 도달
    rebound_reached_1sigma = neckline_price >= df['bb_upper_1'].iloc[neckline_idx] * 0.999
    
    if not rebound_reached_1sigma:
        return {
            "phase": Phase.FIRST_BOTTOM,
            "first_bottom_idx": first_low_idx,
            "first_bottom_price": first_low_price,
            "first_bottom_date": first_low_date,
        }
    
    # 2차 바닥 조건: 마지막 저점이 하단 1σ 근처에서 지지, Higher Low
    second_near_1sigma = last_low_price <= bb_lower_1 * 1.02  # 1σ 근처 (2% 여유)
    higher_low = last_low_price > first_low_price * 0.995  # 첫 저점보다 높음 (0.5% 여유)
    
    if not (second_near_1sigma and higher_low):
        return {
            "phase": Phase.REBOUND,
            "first_bottom_idx": first_low_idx,
            "first_bottom_price": first_low_price,
            "first_bottom_date": first_low_date,
            "neckline_idx": neckline_idx,
            "neckline_price": neckline_price,
        }
    
    # 넥라인 돌파 확인: 현재가가 넥라인 상향 돌파
    breakout = current_price > neckline_price
    
    if breakout:
        # 목표가 = 넥라인 + (넥라인 - 2차 바닥)
        measured_move = neckline_price - last_low_price
        target = neckline_price + measured_move
        # 손절가 = 2차 바닥 저점
        stop = last_low_price
        
        return {
            "phase": Phase.BREAKOUT,
            "signal": SignalType.BUY,
            "first_bottom_idx": first_low_idx,
            "first_bottom_price": first_low_price,
            "first_bottom_date": first_low_date,
            "neckline_idx": neckline_idx,
            "neckline_price": neckline_price,
            "second_bottom_idx": last_low_idx,
            "second_bottom_price": last_low_price,
            "second_bottom_date": last_low_date,
            "entry_price": current_price,
            "stop_price": stop,
            "target_price": target,
            "risk_level": "MEDIUM" if (target - current_price) / (current_price - stop) > 1.5 else "HIGH",
        }
    
    # 넥라인 대기 단계
    return {
        "phase": Phase.NECKLINE_WAIT,
        "first_bottom_idx": first_low_idx,
        "first_bottom_price": first_low_price,
        "first_bottom_date": first_low_date,
        "neckline_idx": neckline_idx,
        "neckline_price": neckline_price,
        "second_bottom_idx": last_low_idx,
        "second_bottom_price": last_low_price,
        "second_bottom_date": last_low_date,
    }


def check_holding_signals(df: pd.DataFrame, state: SignalState) -> Optional[Dict]:
    """보유 중인 포지션의 손절/익절 체크"""
    if state.phase != Phase.HOLDING or state.entry_price is None:
        return None
    
    current_price = df['close'].iloc[-1]
    bb_lower_1 = df['bb_lower_1'].iloc[-1]
    
    # 손절: 2차 바닥 저점 하향 이탈
    if state.stop_price and current_price <= state.stop_price:
        return {
            "signal": SignalType.SELL_STOP,
            "reason": f"손절가 {state.stop_price:,.0f}원 하향 이탈",
            "exit_price": current_price,
        }
    
    # 트레일링 익절: 1σ 밴드 하향 이탈
    if current_price <= bb_lower_1:
        return {
            "signal": SignalType.SELL_TRAIL,
            "reason": f"단기 1σ 밴드({bb_lower_1:,.0f}) 하향 이탈",
            "exit_price": current_price,
        }
    
    return None


def load_signal_states() -> Dict[str, SignalState]:
    """저장된 시그널 상태 로드"""
    state_file = OBSIDIAN_BASE / ".signal_states.json"
    if not state_file.exists():
        return {}
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        states = {}
        for code, v in data.items():
            v['phase'] = Phase(v['phase'])
            v['signal'] = SignalType(v['signal'])
            states[code] = SignalState(**v)
        return states
    except Exception:
        return {}


def save_signal_states(states: Dict[str, SignalState]):
    """시그널 상태 저장"""
    state_file = OBSIDIAN_BASE / ".signal_states.json"
    data = {}
    for code, state in states.items():
        d = asdict(state)
        d['phase'] = state.phase.value
        d['signal'] = state.signal.value
        data[code] = d
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def can_send_signal(code: str, states: Dict[str, SignalState]) -> bool:
    """중복 알림 방지 체크"""
    state = states.get(code)
    if not state or not state.last_signal_time:
        return True
    last = datetime.fromisoformat(state.last_signal_time)
    if last.tzinfo is None:
        last = last.replace(tzinfo=KST)
    return (get_kst_now() - last).total_seconds() > SIGNAL_COOLDOWN_MINUTES * 60


def generate_llm_summary(ticker_info: dict, pattern: dict, signal: SignalType) -> str:
    """시그널 발생 시 LLM용 3줄 요약 프롬프트 생성 (실제 LLM 호출은 Hermes가 담당)"""
    # 이 함수는 프롬프트 문자열만 반환, 실제 LLM 호출은 상위에서 수행
    name = ticker_info['name']
    code = ticker_info['yf'].replace('.KS', '')
    price = pattern.get('entry_price') or pattern.get('exit_price') or 0
    phase_desc = pattern['phase'].name if isinstance(pattern['phase'], Phase) else str(pattern['phase'])
    entry = pattern.get('entry_price', 0)
    stop = pattern.get('stop_price', 0)
    target = pattern.get('target_price', 0)
    risk = pattern.get('risk_level', 'MEDIUM')
    
    if signal == SignalType.BUY:
        signal_str = "매수 신호"
    elif signal == SignalType.SELL_STOP:
        signal_str = "손절 매도"
    elif signal == SignalType.SELL_TRAIL:
        signal_str = "트레일링 익절"
    else:
        signal_str = "보유"
    
    return f"""종목: {name}({code})
현재가: {price:,.0f}원
시그널: {signal_str}
단계: {phase_desc}
진입가: {entry:,.0f}원 | 손절가: {stop:,.0f}원 | 목표가: {target:,.0f}원
리스크: {risk}

→ Telegram용 3줄 요약 생성 (한국어, 이모지 포함)"""


def save_obsidian_note(ticker_info: dict, pattern: dict, signal: SignalType, llm_summary: str):
    """Obsidian에 시그널 노트 저장"""
    code = ticker_info['yf'].replace('.KS', '')
    name = ticker_info['name']
    now = get_kst_now()
    date_str = now.strftime("%Y%m%d")
    
    # 종목 폴더 생성
    stock_dir = OBSIDIAN_BASE / name
    stock_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명
    filename = f"{date_str}_{name}_기술적.md"
    filepath = stock_dir / filename
    
    phase = pattern['phase']
    phase_desc = phase.name if isinstance(phase, Phase) else str(phase)
    
    content = f"""# {name}({code}) 기술적 시그널 - {now.strftime('%Y-%m-%d %H:%M KST')}

**태그**: #기술적분석 #볼린저밴드 #쌍굴파기 #시그널 #{code}

## 시그널 정보
- **시그널**: {signal.value.upper()}
- **단계**: {phase_desc}
- **현재가**: {pattern.get('entry_price') or pattern.get('exit_price', 0):,.0f}원
- **진입가**: {pattern.get('entry_price', 0):,.0f}원
- **손절가**: {pattern.get('stop_price', 0):,.0f}원
- **목표가**: {pattern.get('target_price', 0):,.0f}원
- **리스크**: {pattern.get('risk_level', 'MEDIUM')}

## 패턴 상세
- 1차 바닥: {pattern.get('first_bottom_price', 0):,.0f}원 ({pattern.get('first_bottom_date', 'N/A')})
- 넥라인: {pattern.get('neckline_price', 0):,.0f}원
- 2차 바닥: {pattern.get('second_bottom_price', 0):,.0f}원 ({pattern.get('second_bottom_date', 'N/A')})

## LLM 요약
{llm_summary}

---
*자동 생성: Hermes intraday_monitor.py*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[SAVED] {filepath}")


# ==================== 메인 실행 함수 ====================

def process_ticker(code: str, ticker_info: dict, states: Dict[str, SignalState]) -> Optional[Dict]:
    """단일 종목 처리"""
    yf_symbol = ticker_info['yf']
    name = ticker_info['name']
    
    print(f"[PROCESS] {name}({code})...")
    
    # 1. 데이터 수집
    df = fetch_intraday_data(yf_symbol, days=60)
    if df is None or len(df) < BB_PERIOD + EXTREMA_WINDOW * 2:
        print(f"  데이터 부족: {len(df) if df is not None else 0}봉")
        return None
    
    # 2. 패턴 진단
    pattern = detect_w_pattern_phase(df)
    phase = pattern.get('phase', Phase.NONE)
    
    # 기존 상태 로드
    prev_state = states.get(code)
    
    # 3. 시그널 판단
    signal = SignalType.NONE
    signal_info = None
    
    if phase == Phase.BREAKOUT:
        # 신규 매수 시그널
        if prev_state and prev_state.phase == Phase.HOLDING:
            signal = SignalType.NONE  # 이미 보유 중
        else:
            signal = SignalType.BUY
            signal_info = pattern
    
    elif prev_state and prev_state.phase == Phase.HOLDING:
        # 보유 중인 경우 손절/익절 체크
        hold_check = check_holding_signals(df, prev_state)
        if hold_check:
            signal = hold_check['signal']
            signal_info = {**pattern, **hold_check, 'exit_price': hold_check['exit_price']}
    
    # 4. 상태 업데이트
    new_state = SignalState(
        code=code,
        name=name,
        phase=phase if signal == SignalType.NONE else Phase.HOLDING if signal == SignalType.BUY else phase,
        signal=signal,
        current_price=df['close'].iloc[-1],
        entry_price=pattern.get('entry_price') if signal == SignalType.BUY else (prev_state.entry_price if prev_state else None),
        stop_price=pattern.get('stop_price') if signal == SignalType.BUY else (prev_state.stop_price if prev_state else None),
        target_price=pattern.get('target_price') if signal == SignalType.BUY else (prev_state.target_price if prev_state else None),
        risk_level=pattern.get('risk_level', 'MEDIUM'),
        first_bottom_price=pattern.get('first_bottom_price'),
        first_bottom_date=pattern.get('first_bottom_date'),
        neckline_price=pattern.get('neckline_price'),
        second_bottom_price=pattern.get('second_bottom_price'),
        second_bottom_date=pattern.get('second_bottom_date'),
        last_signal_time=get_kst_now().isoformat() if signal != SignalType.NONE else (prev_state.last_signal_time if prev_state else None),
    )
    states[code] = new_state
    
    # 5. 시그널 발생 시 결과 반환
    if signal != SignalType.NONE and can_send_signal(code, states):
        return {
            'ticker_info': ticker_info,
            'pattern': pattern,
            'signal': signal,
            'state': new_state,
        }
    
    return None


def main():
    print(f"=== 인트라데이 기술적 시그널 감시 시작: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S KST')} ===")
    
    if not is_market_hours():
        print("[SKIP] 장외 시간입니다.")
        return
    
    # 기존 상태 로드
    states = load_signal_states()
    
    # 각 종목 처리
    signals_to_notify = []
    
    for code, info in TICKERS.items():
        try:
            result = process_ticker(code, info, states)
            if result:
                signals_to_notify.append(result)
        except Exception as e:
            print(f"[ERROR] {info['name']}({code}) 처리 실패: {e}")
            continue
        time.sleep(0.2)  # API 호출 간격
    
    # 상태 저장
    save_signal_states(states)
    
    # 시그널 발생 종목에 대해 LLM 요약 생성 프롬프트 출력
    if signals_to_notify:
        print(f"\n=== 시그널 발생: {len(signals_to_notify)}종목 ===")
        for sig in signals_to_notify:
            prompt = generate_llm_summary(sig['ticker_info'], sig['pattern'], sig['signal'])
            print(f"\n--- LLM PROMPT for {sig['ticker_info']['name']} ---")
            print(prompt)
            print("--- END PROMPT ---\n")
            
            # 실제로는 Hermes가 이 프롬프트를 LLM에 전달하고 결과를 받아 Telegram 전송
            # 여기서는 프롬프트만 출력 (Hermes가 처리)
    else:
        print("[INFO] 금회 시그널 없음")
    
    print(f"=== 완료: {get_kst_now().strftime('%H:%M:%S')} ===")


if __name__ == "__main__":
    main()