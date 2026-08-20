import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 20종목 정의
TICKERS = {
    # 국내 12개
    "005930.KS": {"name": "삼성전자", "code": "005930", "market": "KR"},
    "000660.KS": {"name": "SK하이닉스", "code": "000660", "market": "KR"},
    "011790.KS": {"name": "SKC", "code": "011790", "market": "KR"},
    "046970.KS": {"name": "우리로", "code": "046970", "market": "KR"},
    "252670.KS": {"name": "KODEX 200", "code": "252670", "market": "KR"},
    "453830.KS": {"name": "TIGER K방산&우주", "code": "453830", "market": "KR"},
    "225460.KS": {"name": "토박스코리아", "code": "225460", "market": "KR"},
    "373220.KS": {"name": "LG에너지솔루션", "code": "373220", "market": "KR"},
    "006400.KS": {"name": "삼성SDI", "code": "006400", "market": "KR"},
    "035420.KS": {"name": "NAVER", "code": "035420", "market": "KR"},
    "035720.KS": {"name": "카카오", "code": "035720", "market": "KR"},
    "005380.KS": {"name": "현대차", "code": "005380", "market": "KR"},
    # 해외 8개
    "NVDA": {"name": "NVDA", "code": "NVDA", "market": "US"},
    "NVDY": {"name": "NVDY", "code": "NVDY", "market": "US"},
    "QQQ": {"name": "QQQ", "code": "QQQ", "market": "US"},
    "TQQQ": {"name": "TQQQ", "code": "TQQQ", "market": "US"},
    "AAPL": {"name": "AAPL", "code": "AAPL", "market": "US"},
    "MSFT": {"name": "MSFT", "code": "MSFT", "market": "US"},
    "GOOGL": {"name": "GOOGL", "code": "GOOGL", "market": "US"},
    "AMZN": {"name": "AMZN", "code": "AMZN", "market": "US"},
}

# 시그널 중복 방지용 (파일 기반 영속성)
SIGNAL_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'signal_cache.json')

def load_signal_cache():
    """시그널 캐시 로드 (1시간 내 중복 방지)"""
    if os.path.exists(SIGNAL_CACHE_FILE):
        with open(SIGNAL_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_signal_cache(cache):
    """시그널 캐시 저장"""
    with open(SIGNAL_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def is_duplicate_signal(cache, ticker, signal, phase):
    """동일 종목 동일 시그널 1시간 내 재발송 방지"""
    key = f"{ticker}_{signal}_{phase}"
    now = datetime.now().timestamp()
    if key in cache:
        last_time = cache[key]
        if now - last_time < 3600:  # 1시간
            return True
    cache[key] = now
    return False

def fetch_price_data(ticker, period="60d", interval="30m"):
    """30분봉 데이터 수집 (최근 60일) - MultiIndex 컬럼 처리 포함"""
    try:
        # multi_level_index=False로 MultiIndex 방지
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True, multi_level_index=False)
        if df.empty:
            return None
        df = df.reset_index()
        # 컬럼명 정규화 (MultiIndex 처리)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() if c[0] else c[1].lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]
        if 'datetime' in df.columns:
            df = df.rename(columns={'datetime': 'date'})
        elif 'date' not in df.columns and 'index' in df.columns:
            df = df.rename(columns={'index': 'date'})
        df['date'] = pd.to_datetime(df['date'])
        # 필요한 컬럼만 선택
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        available_cols = [c for c in required_cols if c in df.columns]
        if len(available_cols) < 6:
            print(f"  -> Missing columns for {ticker}: {df.columns.tolist()}")
            return None
        return df[required_cols].dropna()
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def calculate_indicators(df):
    """이중 볼린저밴드 계산"""
    # BB(20, 2.0)
    df['bb20_2_mid'] = df['close'].rolling(20).mean()
    df['bb20_2_std'] = df['close'].rolling(20).std()
    df['bb20_2_upper'] = df['bb20_2_mid'] + 2.0 * df['bb20_2_std']
    df['bb20_2_lower'] = df['bb20_2_mid'] - 2.0 * df['bb20_2_std']
    
    # BB(20, 1.0)
    df['bb20_1_mid'] = df['bb20_2_mid']  # 같은 20일 이동평균
    df['bb20_1_upper'] = df['bb20_1_mid'] + 1.0 * df['bb20_2_std']
    df['bb20_1_lower'] = df['bb20_1_mid'] - 1.0 * df['bb20_2_std']
    
    # 로컬 최저점/최고점 (window=5, center=True)
    df['local_min'] = df['low'].rolling(5, center=True).min() == df['low']
    df['local_max'] = df['high'].rolling(5, center=True).max() == df['high']
    
    return df

def detect_w_pattern_phase(df):
    """W-패턴 현재 단계 진단 (6단계 상태 머신)"""
    if len(df) < 25:
        return {"phase": 0, "phase_desc": "데이터 부족", "details": {}}
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    recent = df.tail(30)
    
    # 로컬 최저점/최고점 찾기
    local_mins = recent[recent['local_min']].copy()
    local_maxs = recent[recent['local_max']].copy()
    
    # 1차 바닥 후보: 하단밴드 2σ 터치/이탈 후 반등
    first_bottom_candidates = local_mins[local_mins['low'] <= local_mins['bb20_2_lower'] * 1.002]
    
    # 중간 고점 후보: 상단밴드 1σ 이상 도달
    middle_peak_candidates = local_maxs[local_maxs['high'] >= local_maxs['bb20_1_upper'] * 0.998]
    
    # 2차 바닥 후보: 하단밴드 1σ 근처 지지
    second_bottom_candidates = local_mins[
        (local_mins['low'] >= local_mins['bb20_1_lower'] * 0.995) & 
        (local_mins['low'] <= local_mins['bb20_1_lower'] * 1.01)
    ]
    
    phase = 0
    phase_desc = "패턴 없음"
    details = {}
    
    if len(first_bottom_candidates) > 0:
        first_bottom = first_bottom_candidates.iloc[-1]
        first_bottom_idx = first_bottom.name
        first_bottom_price = first_bottom['low']
        first_bottom_date = first_bottom['date']
        details['first_bottom'] = {'price': float(first_bottom_price), 'date': str(first_bottom_date)}
        
        # 1차 바닥 이후 중간 고점 확인
        after_first = recent[recent.index > first_bottom_idx]
        middle_peaks = after_first[after_first['local_max']]
        valid_middle = middle_peaks[middle_peaks['high'] >= middle_peaks['bb20_1_upper'] * 0.998]
        
        if len(valid_middle) > 0:
            middle_peak = valid_middle.iloc[-1]
            middle_peak_idx = middle_peak.name
            middle_peak_price = middle_peak['high']
            middle_peak_date = middle_peak['date']
            details['middle_peak'] = {'price': float(middle_peak_price), 'date': str(middle_peak_date)}
            
            # 2차 바닥 후보 (중간 고점 이후)
            after_middle = recent[recent.index > middle_peak_idx]
            second_bottoms = after_middle[after_middle['local_min']]
            valid_second = second_bottoms[
                (second_bottoms['low'] >= second_bottoms['bb20_1_lower'] * 0.995) & 
                (second_bottoms['low'] <= second_bottoms['bb20_1_lower'] * 1.01)
            ]
            
            if len(valid_second) > 0:
                second_bottom = valid_second.iloc[-1]
                second_bottom_price = second_bottom['low']
                second_bottom_date = second_bottom['date']
                details['second_bottom'] = {'price': float(second_bottom_price), 'date': str(second_bottom_date)}
                
                # Higher Low 확인
                if second_bottom_price > first_bottom_price:
                    phase = 3
                    phase_desc = "2차 바닥 형성 중 (Higher Low 확인)"
                    details['higher_low'] = True
                    details['neckline'] = float(middle_peak_price)
                else:
                    phase = 2
                    phase_desc = "2차 바닥 형성 중 (Higher Low 미확인)"
                    details['higher_low'] = False
            else:
                phase = 2
                phase_desc = "중간 반등 완료, 2차 바닥 대기"
                details['neckline'] = float(middle_peak_price)
        else:
            phase = 1
            phase_desc = "1차 바닥 형성, 중간 반등 대기"
    else:
        # 현재가가 하단밴드 2σ 근처인지 확인 (1차 바닥 형성 가능성)
        if last['low'] <= last['bb20_2_lower'] * 1.005:
            phase = 1
            phase_desc = "1차 바닥 형성 가능성 (하단밴드 2σ 근접)"
    
    # 넥라인 돌파 확인 (단계 5)
    if phase >= 3 and 'neckline' in details:
        neckline = details['neckline']
        if last['close'] > neckline and prev['close'] <= neckline:
            phase = 5
            phase_desc = "넥라인 돌파 확인 → 매수 시그널"
            details['entry_price'] = float(last['close'])
            details['stop_loss'] = float(details['second_bottom']['price'])
            details['target_price'] = float(neckline + (neckline - details['second_bottom']['price']))
        elif last['close'] > neckline:
            phase = 4
            phase_desc = "넥라인 돌파 대기 (이미 돌파됨)"
            details['entry_price'] = float(neckline)
            details['stop_loss'] = float(details['second_bottom']['price'])
            details['target_price'] = float(neckline + (neckline - details['second_bottom']['price']))
    
    # 보유 중 손절/익절 확인 (단계 6)
    if phase == 5:
        # 손절: 2차 바닥 저점 하향 이탈
        if last['close'] < details['stop_loss']:
            phase = 6
            phase_desc = "손절 시그널 (2차 바닥 이탈)"
        # 트레일링: 1σ 밴드 하향 이탈
        elif last['close'] < last['bb20_1_lower']:
            phase = 6
            phase_desc = "트레일링 익절 (1σ 밴드 이탈)"
    
    return {"phase": phase, "phase_desc": phase_desc, "details": details, "current_price": float(last['close'])}

def generate_signal(phase_info):
    """단계별 시그널 결정"""
    phase = phase_info['phase']
    if phase == 5:
        return "BUY"
    elif phase == 6:
        return "SELL"
    else:
        return "HOLD"

def format_price(price, market):
    """가격 포맷 (KRW/USD)"""
    if market == "KR":
        return f"{price:,.0f}원"
    else:
        return f"${price:,.2f}"

def format_signal_summary(result):
    """Telegram용 3줄 요약 생성 (LLM 프롬프트 템플릿)"""
    name = result['name']
    code = result['code']
    market = result['market']
    price = result['current_price']
    phase = result['phase']
    phase_desc = result['phase_desc']
    signal = result['signal']
    details = result['details']
    
    price_str = format_price(price, market)
    
    if signal == "BUY":
        entry = format_price(details.get('entry_price', price), market)
        stop = format_price(details.get('stop_loss', 0), market)
        target = format_price(details.get('target_price', 0), market)
        risk = "HIGH" if phase == 5 else "MEDIUM"
        
        return f"""🔔 [기술적 시그널] {name}({code}) - 매수 신호
현재가: {price_str} | 단계: {phase_desc}(단계{phase})
진입: {entry} | 손절: {stop} | 목표: {target}
리스크: {risk} | 30분봉 BB(20,2)+BB(20,1)"""
    
    elif signal == "SELL":
        return f"""🔔 [기술적 시그널] {name}({code}) - 매도 신호
현재가: {price_str} | 단계: {phase_desc}(단계{phase})
사유: {'손절 (2차 바닥 이탈)' if '손절' in phase_desc else '트레일링 익절 (1σ 밴드 이탈)'}
리스크: HIGH | 30분봉 BB(20,2)+BB(20,1)"""
    
    return None

# 메인 실행
def main():
    signal_cache = load_signal_cache()
    results = []
    signals_found = []
    
    print(f"=== 기술적 시그널 감시 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    for ticker, info in TICKERS.items():
        print(f"Processing {ticker} ({info['name']})...")
        df = fetch_price_data(ticker)
        if df is None or len(df) < 25:
            print(f"  -> 데이터 부족 또는 에러")
            continue
        
        df = calculate_indicators(df)
        phase_info = detect_w_pattern_phase(df)
        signal = generate_signal(phase_info)
        
        result = {
            "ticker": ticker,
            "name": info['name'],
            "code": info['code'],
            "market": info['market'],
            "current_price": phase_info['current_price'],
            "phase": phase_info['phase'],
            "phase_desc": phase_info['phase_desc'],
            "signal": signal,
            "details": phase_info['details']
        }
        results.append(result)
        
        # 중복 시그널 체크
        if signal in ["BUY", "SELL"]:
            if not is_duplicate_signal(signal_cache, ticker, signal, phase_info['phase']):
                signals_found.append(result)
                print(f"  -> *** SIGNAL: {signal} *** Phase {phase_info['phase']}: {phase_info['phase_desc']}")
            else:
                print(f"  -> 중복 시그널 억제: {signal} Phase {phase_info['phase']}")
        else:
            print(f"  -> Phase {phase_info['phase']}: {phase_info['phase_desc']} (HOLD)")
    
    # 시그널 캐시 저장
    save_signal_cache(signal_cache)
    
    print(f"\n=== 총 {len(results)}종목 분석 완료, 신규 시그널: {len(signals_found)}개 ===")
    
    # Telegram 알림용 요약 출력
    for s in signals_found:
        summary = format_signal_summary(s)
        if summary:
            print(f"\n--- TELEGRAM ALERT ---\n{summary}\n---------------------")
    
    # 결과 JSON 출력 (파이프라인 연동용)
    output = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "signals": signals_found
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()