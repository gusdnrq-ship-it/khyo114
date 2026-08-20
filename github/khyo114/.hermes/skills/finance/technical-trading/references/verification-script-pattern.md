# Ad-hoc Verification Script Pattern for technical-trading

## 목적
백테스트 핵심 함수(지표 계산, 패턴 탐지, 백테스트 엔진, 시그널 진단)가 코드 변경 후에도 정상 작동하는지 빠르게 검증하기 위한 표준 패턴.

## 검증 대상 함수 (run_daily_backtest.py 기준)
1. `calculate_bollinger_bands` — 볼린저밴드 지표 계산, NaN 처리
2. `detect_local_extrema` — 로컬 고점/저점 탐지
3. `detect_w_pattern` — W-패턴(쌍바닥) 탐지
4. `run_backtest` — 백테스트 엔진 (수수료/슬리피지 반영)
5. `check_current_signal` — 현재 시그널 단계 진단

## 검증 스크립트 위치
- **메인**: `scripts/verify_backtest.py` (run_daily_backtest.py에서 import)
- **템플릿**: 이 문서 (references/verification-script-pattern.md)

## 실행 방법
```bash
# 스킬 디렉토리에서 실행
cd /c/Users/kho/AppData/Local/hermes/skills/finance/technical-trading
python scripts/verify_backtest.py

# 또는 임시 파일로 저장 후 실행 (임시 검증용)
cd /c/Users/Public/Documents/ESTsoft/CreatorTemp
python hermes-verify-backtest.py
```

## 검증 기준 (Pass 조건)
- 모든 5개 테스트 통과
- NaN 값 없음 (지표 계산 후 유효 구간에서)
- 지표 논리적 일관성 (상단 > 중단 > 하단, 2σ > 1σ)
- 백테스트 결과 구조 완전성 (total_trades, win_rate, avg_return, max_drawdown, sharpe_ratio, final_equity, trades)
- 시그널 단계 7개 중 하나 반환 (0=NONE ~ 6=HOLDING)

## 이 세션에서 발견된 이슈 및 수정 (2026-08-20)
| 이슈 | 원인 | 수정 |
|------|------|------|
| `calculate_bollinger_bands` NaN 잔존 | `dropna`를 `Close` 기준 수행 후 지표 계산 | 지표 계산 후 `BB_20_2_mid` 기준 `dropna`로 이동 |
| 엔비디아 NaN 출력 | rolling(20) 초기 19행 NaN이 최종 행까지 전파 | 위 수정으로 해결됨 |
| 우리로(046970) IndexError | yfinance에서 21일만 제공 → 60일 미만으로 패턴 탐지 단계에서 out-of-bounds | 데이터 충분성 체크(`len(df) < 60`) 추가 및 `continue`로 스킵 |

## 검증 스크립트 핵심 패턴
```python
# 1. 합성 데이터 생성 (고정 시드 42로 재현성 보장)
def create_test_data(days=100, trend='up', seed=42):
    ...

# 2. 각 함수 단위 테스트
def test_calculate_bollinger_bands():
    df = create_test_data(50)
    bb_u2, bb_m2, bb_l2 = calculate_bollinger_bands(df, 20, 2.0)
    # 유효 구간만 테스트
    valid_start = max(bb_l2.first_valid_index(), bb_l1.first_valid_index())
    ...
    assert not bb_m2.isna().any()
    assert (bb_u2 > bb_m2).all() and (bb_m2 > bb_l2).all()
    ...

# 3. 백테스트 엔진은 mock 시그널로 테스트
def test_run_backtest():
    mock_signals = [{...}]  # 알려진 패턴 구조
    result = run_backtest(mock_signals, df_valid)
    assert result['total_trades'] == 1
    ...
```

## 향후 유지보수 포인트
- `run_daily_backtest.py` 함수 시그니처 변경 시 `verify_backtest.py` 동기화 필요
- 새로운 전략 추가 시 해당 전략 검증 테스트 케이스 추가
- 합성 데이터 시드(42) 고정으로 재현성 보장
- 실데이터 기반 회귀 테스트는 별도 스크립트로 관리 (`scripts/regression_test.py` 예정)