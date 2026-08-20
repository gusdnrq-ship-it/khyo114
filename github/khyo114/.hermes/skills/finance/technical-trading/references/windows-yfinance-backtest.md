# Windows/WSL 환경에서 technical-trading 실행 노하우 (2026-08-17 세션)

## 데이터 소스: yfinance 사용 (FinanceDataReader 미작동)

### 문제
- `FinanceDataReader` → `ModuleNotFoundError` 또는 `exit -1` 발생
- Windows + Hermes 환경에서 import 실패

### 해결: yfinance 사용
```python
import yfinance as yf

# 한국 주식: 종목코드 + .KS 접미사
ticker = "005930.KS"  # 삼성전자
df = yf.download(ticker, start="2021-01-01", end="2026-08-13", progress=False)

# 해외 주식: 그대로 사용
ticker = "NVDA"
df = yf.download(ticker, start="2021-01-01", end="2026-08-13", progress=False)
```

### 설치
```bash
pip install yfinance
# Hermes venv: /home/kho/.hermes/hermes-agent/venv/bin/pip install yfinance
```

## 백테스트 실행 워크플로우 (이 세션에서 검증)

### 1. 가격 데이터 수집
```python
def fetch_price_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """yfinance로 일봉 데이터 수집"""
    suffix = ".KS" if symbol.isdigit() and len(symbol) == 6 else ""
    df = yf.download(f"{symbol}{suffix}", start=start, end=end, progress=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]  # MultiIndex 평탄화
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
```

### 2. 볼린저밴드 지표 계산
```python
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """BB(20,2) + BB(20,1) 계산"""
    df = df.copy()
    df['BB_20_2_mid'] = df['Close'].rolling(20).mean()
    df['BB_20_2_std'] = df['Close'].rolling(20).std()
    df['BB_20_2_upper'] = df['BB_20_2_mid'] + 2 * df['BB_20_2_std']
    df['BB_20_2_lower'] = df['BB_20_2_mid'] - 2 * df['BB_20_2_std']
    
    df['BB_20_1_upper'] = df['BB_20_2_mid'] + 1 * df['BB_20_2_std']
    df['BB_20_1_lower'] = df['BB_20_2_mid'] - 1 * df['BB_20_2_std']
    return df
```

### 3. W-패턴(쌍바닥) 탐지 로직
```python
def detect_w_pattern(df: pd.DataFrame) -> list[dict]:
    """로컬 최저점 기반 W 패턴 탐지"""
    signals = []
    # 1차 바닥: 종가 <= BB_20_2_lower
    # 중간 반등: 종가 >= BB_20_1_upper
    # 2차 바닥: 종가 근처 BB_20_1_lower, Higher Low 조건
    # 넥라인 돌파: 중간 고점 상향 돌파 시 매수
    # 구현 생략 - skill 본문 참조
    return signals
```

## Windows 경로/인코딩 주의사항

### 경로 구분자
```python
# Good - 포워드 슬래시
data_dir = "C:/Users/kho/주식분석/data"

# Good - raw string
data_dir = r"C:\Users\kho\주식분석\data"

# Bad - 이스케이프 깨짐
data_dir = "C:\Users\kho\주식분석\data"  # \u, \주 등 해석됨
```

### 인코딩 강제
```bash
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8
export PYTHONIOENCODING=utf-8
```
`config.yaml`에 추가:
```yaml
terminal:
  env:
    LANG: "ko_KR.UTF-8"
    LC_ALL: "ko_KR.UTF-8"
    PYTHONIOENCODING: "utf-8"
```

## Obsidian 저장 경로 패턴
```
주식분석/
├── YYYYMMDD_종합투자분석리포트.md
├── 삼성전자/
│   ├── YYYYMMDD_삼성전자.md                    # 펀더멘털
│   └── YYYYMMDD_삼성전자_백테스트_쌍굴파기.md  # 기술적
├── NVDA/
│   ├── YYYYMMDD_엔비디아.md
│   └── YYYYMMDD_엔비디아_백테스트_쌍굴파기.md
└── ...
```

## 태그 규칙
- 펀더멘털: `#주식분석 #종목코드 #섹터 #시장구분 #투자리포트`
- 기술적: `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}`

## 검증된 종목 리스트 (이 세션)
| 종목 | 코드 | 비고 |
|------|------|------|
| 삼성전자 | 005930 | 대장주, 유동성 풍부 |
| NVDA | NVDA | 해외 반도체 대장주 |
| 우리로 | 046970 | 전략 원 검증 종목 (4.5년 1회 신호, 손실) |
| SKC | 011790 | 2차전지 소재, 변동성 큼 |
| TIGER K방산&우주 | 453830 | 방산/우주 테마 ETF |