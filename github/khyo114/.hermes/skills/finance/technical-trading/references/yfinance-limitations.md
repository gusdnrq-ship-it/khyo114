# yfinance 한국 주식 데이터 수집 한계 및 대응 방안

## 검증된 한계 (2026-08-18 세션)

### 1. 한국 ETF 티커 미지원
| 종목 | 코드 | 시도 티커 | 결과 |
|------|------|-----------|------|
| TIGER K방산&우주 | 453830 | 453830.KS | HTTP 404 Not Found |
| KODEX 200 | 252670 | 252670.KS | 데이터 수집 성공하나 지표 부족 |

**원인**: yfinance가 한국 ETF 전 종목을 커버하지 않음. 상장 직후 ETF나 테마형 ETF는 미등록일 수 있음.

**대응**:
- 네이버 금융 API(`chart.naver.com/item/main.nhn?code=453830`)로 JSON 데이터 수집
- `curl -H "User-Agent: Mozilla/5.0" "https://chart.naver.com/item/main.nhn?code=453830" > data/naver_chart_453830.json`
- KRX 공식 데이터(`data.krx.co.kr`) 활용 검토

### 2. 소형주/신규상장주 데이터 기간 제한
| 종목 | 코드 | 수집 기간 | 비고 |
|------|------|-----------|------|
| 우리로 | 046970 | 21일만 (2026-07-16 ~) | 최소 3년 필요하나 최근분만 제공 |

**원인**: yfinance가 특정 소형주에 대해 전체 히스토리를 제공하지 않음.

**대응**:
- 네이버 금융 일봉 차트 API로 장기 데이터 보완
- `https://api.stock.naver.com/chart/domestic/item/046970/day?count=1000` 활용
- FinanceDataReader 대안 모색 (현재 환경 미작동)

### 3. MultiIndex 컬럼 평탄화 필요
```python
# yfinance 최신 버전 반환 형태
df.columns = [('Open', '005930.KS'), ('High', '005930.KS'), ...]

# 평탄화 필요
df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
# 또는
df.columns = df.columns.droplevel(1)
```

### 4. auto_adjust 기본값 변경 주의
```python
# 분봉/일봉 분할 조정 여부
df = yf.download(ticker, start, end, auto_adjust=False)  # 미조정 가격 (배당/분할 반영 안됨)
df = yf.download(ticker, start, end, auto_adjust=True)   # 조정 가격 (기본값, 버전별 다름)
```

### 5. 진행바 출력 억제
```python
df = yf.download(ticker, start, end, progress=False)  # 로그 깨짐 방지
```

## 권장 데이터 수집 패턴 (한국 주식)

```python
import yfinance as yf
import pandas as pd

def fetch_korea_stock(symbol: str, start: str, end: str) -> pd.DataFrame:
    """한국 주식(코스피/코스닥) 데이터 수집 with fallback"""
    # 1차: yfinance 시도
    ticker = f"{symbol}.KS"  # 코스피 가정
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    
    if df.empty or len(df) < 250:  # 1년 미만이면 fallback
        # 2차: 네이버 금융 API
        df = fetch_from_naver(symbol)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

def fetch_from_naver(symbol: str) -> pd.DataFrame:
    """네이버 금융 일봉 차트 API (비공식)"""
    import json
    url = f"https://api.stock.naver.com/chart/domestic/item/{symbol}/day?count=1000"
    # curl 또는 requests로 수집 후 DataFrame 변환
    pass
```

## 이 세션 검증 결과
| 종목 | yfinance 상태 | 비고 |
|------|---------------|------|
| 삼성전자(005930) | ✅ 1374일 (5.5년) | 정상 |
| SKC(011790) | ✅ 1374일 | 정상 |
| 엔비디아(NVDA) | ✅ 1411일 | 해외주식 정상 |
| 우리로(046970) | ⚠️ 21일만 | 소형주 한계 |
| TIGER K방산우주(453830) | ❌ 404 에러 | ETF 미지원 |

## 2026-08-19 Intraday 30m Monitoring Session — 추가 확인된 한계
| 종목 | 코드 | 시도 티커 | 30분봉 결과 | 원인 | 대안 |
|------|------|-----------|-------------|------|------|
| 우리로 | 046970 | 046970.KS | ❌ KeyError: tradingPeriods | 소형주, 거래 기간 데이터 미제공 | 일봉 데이터 + 수동 30분 근사 |
| TIGER K방산&우주 | 453830 | 453830.KS | ❌ HTTP 404 | 한국 테마형 ETF 미등록 | 일봉 타임프레임 또는 네이버 금융 |
| 토박스코리아 | 225460 | 225460.KS | ❌ HTTP 404 | 소형주, 30분봉 미지원 | 일봉 타임프레임 또는 네이버 금융 |

**핵심 인사이트**: yfinance 30분봉 한국 주식 지원은 대형주(코스피200 구성종목급) 위주로 한정됨. 소형주/테마형 ETF는 일봉 폴백 또는 대체 데이터 소스(네이버 금융 API) 필수.

## 향후 개선 로드맵
1. **네이버 금융 API 래퍼** 구현 (`scripts/naver_price_fetcher.py`)
2. **데이터 소스 폴백 체인** 자동화 (yfinance → 네이버 → KRX)
3. **ETF 전용 지표** 수집 추가 (NAV, 추적오차, 운용보수)
4. **데이터 품질 검증** (결측일, 이상치, 분할/배당 조정 확인)

## 관련 참고 문서
- `references/windows-python-env.md` — Windows Python 환경 필수 사항 (venv Python 3.11 사용 필수)
- `references/intraday-30m-monitoring.md` — 30분봉 모니터링 아키텍처 및 패턴
- `references/session-2026-08-19-intraday-monitoring.md` — 2026-08-19 실행 로그 및 결과