# yfinance로 한국 주식 데이터 수집 (검증된 패턴)

## 배경
- FinanceDataReader 현재 환경에서 미작동 (import 오류, exit -1)
- yfinance가 한국 주식(005930.KS) 지원하며 안정적으로 동작 확인

## 검증된 코드 패턴

```python
import yfinance as yf
import pandas as pd

# 삼성전자 데이터 수집 (2021-01-01 ~ 2026-08-13)
df = yf.download('005930.KS', start='2021-01-01', end='2026-08-13', progress=False)

# 컬럼 정리 (MultiIndex → 단일 컬럼)
df.columns = df.columns.droplevel(1)  # ('Open', '005930.KS') → 'Open'

# 필요한 컬럼만 선택
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

# CSV 저장
df.to_csv('C:/Users/kho/samsung_005930_2021_2026.csv')
print(f'데이터 수집 완료: {len(df)}일')
print(f'기간: {df.index[0].date()} ~ {df.index[-1].date()}')
```

## 주의사항
1. **티커 형식**: 한국 주식은 `.KS`(코스피) 또는 `.KQ`(코스닥) 접미사 필수
2. **MultiIndex 컬럼**: yfinance 최신 버전은 MultiIndex 반환 → `.droplevel(1)`로 평탄화 필요
3. **progress=False**: 진행바 출력 억제 (로그 깨짐 방지)
4. **날짜 인덱스**: UTC 기준 → 한국 시간 고려 시 주의

## 설치
```bash
pip install yfinance pandas
```

## 테스트 결과 (2026-08-13)
- 종목: 삼성전자(005930.KS)
- 기간: 2021-01-01 ~ 2026-08-13 (약 5.5년, ~1,400거래일)
- 수집 성공: ✅
- CSV 저장: ✅