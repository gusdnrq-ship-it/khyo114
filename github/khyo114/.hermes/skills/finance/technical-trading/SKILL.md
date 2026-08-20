---
name: technical-trading
description: 기술적 매매기법 백테스트 및 시그널 진단 - 쌍굴파기 이중 볼린저밴드 전략 등 차트 기반 매매기법을 실제 가격 데이터로 검증
version: "1.0"
author: Hermes Agent
tags: [backtesting, technical-analysis, bollinger-bands, trading-signals, korean-stocks]
---

# Technical Trading Skill - 기술적 매매기법 백테스트

## 목적
유튜브/서적에서 학습한 기술적 매매기법을 **실제 종목 가격 데이터로 백테스트**하고, **현재 매수/매도 시그널 상태를 진단**한다.
- 펀더멘털 분석(stock-analysis)과 완전히 분리
- "자료 정리"가 아니라 **실데이터 검증**이 핵심

## 트리거 조건
- "백테스트", "기술적 분석", "볼린저밴드", "쌍굴파기", "눌림매매", "매매기법 검증", "시그널 확인", "매수 타이밍" 등 키워드 포함 시

## 전략 레지스트리 (확장 가능)

### 전략 1: 쌍굴파기 이중 볼린저밴드 (W-Pattern Double Bollinger Bands)
**출처**: 유튜브 기술적 분석 채널 (구체적 출처는 사용자 제공)
**검증 종목**: 우리로(046970) - 4.5년 데이터 기준 1회 신호 발생, 손실 기록됨

#### 지표 설정
- **볼린저밴드 1 (중기)**: 20일 이동평균, 표준편차 2.0
- **볼린저밴드 2 (단기)**: 20일 이동평균, 표준편차 1.0
- **쌍바닥(W) 조건**:
  1. 첫 번째 바닥: 가격이 하단 밴드(2σ) 터치 또는 하회 후 반등
  2. 중간 반등: 가격이 상단 밴드(1σ) 이상 도달
  3. 두 번째 바닥: 가격이 하단 밴드(1σ) 근처에서 지지받고 반등 (첫 바닥보다 높아야 함 = Higher Low)
  4. 돌파 확인: 중간 고점(넥라인) 상향 돌파 시 매수 진입

#### 진입/청산 규칙
- **진입**: 넥라인(중간 고점) 상향 돌파 시 종가 기준 매수
- **손절**: 두 번째 바닥 저점 하향 이탈 시
- **목표가**: 넥라인 - 두 번째 바닥 저점 거리만큼 상향 투영 (Measured Move)
- **트레일링**: 수익 발생 시 1σ 밴드 하향 이탈 시 부분 익절

#### 백테스트 파라미터
- 데이터 기간: 최소 3년 이상 일봉 데이터
- 수수료: 0.015% (한국 주식 기준)
- 슬리피지: 0.1%
- 포지션 크기: 고정 비율 (예: 자산 10%)

## 필수 기능

### 1. 데이터 수집 (`fetch_price_data`)
```python
# 입력: 종목코드(6자리), 시작일, 종료일
# 출력: DataFrame[Date, Open, High, Low, Close, Volume]
# 소스: 네이버 금융, KRX, Yahoo Finance 등 (브라우저 미사용)
```

### 2. 지표 계산 (`calculate_indicators`)
```python
# 입력: 가격 DataFrame
# 출력: BB_20_2_upper, BB_20_2_lower, BB_20_2_mid, BB_20_1_upper, BB_20_1_lower, BB_20_1_mid 컬럼 추가
```

### 3. 패턴 탐지 (`detect_w_pattern`)
```python
# 입력: 지표 포함 DataFrame
# 출력: 시그널 리스트 [{date, type: 'buy'|'sell', price, pattern_info}]
# 로직: 로컬 최저점 탐지 -> W 패턴 조건 검증 -> 넥라인 돌파 확인
```

### 4. 백테스트 엔진 (`run_backtest`)
```python
# 입력: 시그널 리스트, 가격 데이터, 파라미터(수수료, 슬리피지)
# 출력: 
#   - 총 거래 횟수, 승률, 평균 수익률, MDD, 샤프 비율
#   - 거래별 상세 내역 (진입/청산일, 가격, 수익률, 보유일수)
#   - 누적 수익률 차트 데이터
```

### 5. 현재 시그널 진단 (`check_current_signal`)
```python
# 입력: 최신 데이터 (최근 60일)
# 출력: 
#   - 현재 패턴 형성 단계 (1차 바닥, 반등 중, 2차 바닥 형성 중, 넥라인 대기, 돌파 확인)
#   - 매수/매도 시그널 여부, 진입가/손절가/목표가
#   - 리스크 레벨 (높음/보통/낮음)
```

## 실행 워크플로우

### 백테스트 모드
```
사용자: "삼성전자 쌍굴파기 이중 볼린저밴드 백테스트 해줘"
1. fetch_price_data("005930", "2021-01-01", "2026-08-13")
2. calculate_indicators(df)
3. signals = detect_w_pattern(df)
4. results = run_backtest(signals, df)
5. 결과 리포트 출력 + 차트 저장 (옵시디언)
```

### 시그널 진단 모드
```
사용자: "우리로 현재 쌍굴파기 시그널 있어?"
1. fetch_price_data("046970", "2024-01-01", "2026-08-13")  # 최근 2년
2. calculate_indicators(df)
3. status = check_current_signal(df)
4. 현재 단계, 시그널 여부, 진입가/손절가/목표가 안내
```

### 통합 파이프라인 연동 (hermes-stock-pipeline과 함께)

매일 09:30 KST 크론 잡에서 **펀더멘털 분석(stock-analysis) 후 자동 실행**:

```bash
# hermes-stock-pipeline 크론 잡 예시 (통합)
hermes cron create "30 9 * * *" \
  "통합 주식분석 파이프라인 실행..." \
  --skill stock-analysis,technical-trading,hermes-stock-pipeline \
  --model google/gemini-2.5-flash-lite \
  --provider openrouter \
  --deliver origin,telegram:6723387878
```

**자동 실행 시 동작:**
1. 핵심 5종목(삼성전자, NVDA, 우리로, SKC, TIGER K방산&우주) 대상
2. yfinance로 최근 3년 일봉 수집 → BB(20,2)+BB(20,1) 계산
3. W-패턴 탐지 → 백테스트(수수료 0.015%, 슬리피지 0.1%)
4. 현재 시그널 단계 진단
5. 결과 저장: `주식분석/{종목명}/{YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md`
   태그: `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}`
6. Telegram으로 요약 알림 (시그널 여부, 진입가/손절가/목표가, 리스크 레벨)

## 출력 형식 (옵시디언 저장 시)
```
파일명: {YYYYMMDD}_{종목명}_백테스트_{전략명}.md
태그: 기술적분석, 백테스트, 볼린저밴드, 쌍굴파기, {종목코드}

내용:
- 전략 개요 및 파라미터
- 백테스트 기간, 데이터 소스
- 핵심 지표 (승률, 수익률, MDD, 샤프, 거래횟수)
- 거래 내역 테이블
- 누적 수익률 차트 (base64 이미지 또는 링크)
- 현재 시그널 상태 (진단 모드 시)
- 주의사항 (과적합 경고, 표본 수 부족 등)
```

## 데이터 소스 우선순위 (브라우저 미사용)
1. **Yahoo Finance (yfinance)** - 한국 주식(005930.KS) 지원, 가장 안정적, pip install yfinance로 설치 가능
2. **네이버 금융 API** (chart.naver.com/item/main.nhn 등) - curl로 JSON 수집
3. **KRX 데이터** (data.krx.co.kr) - 공식 데이터
4. **FinanceDataReader** - 현재 환경에서 동작하지 않음 (import 오류), 비추천
## 환경별 주의사항 (Windows + Hermes)

- **FinanceDataReader 미작동**: `ModuleNotFoundError` 또는 `exit -1` 발생 → yfinance 사용 권장
- **UnicodeDecodeError**: Windows 콘솔 CP949 vs UTF-8 충돌 → 터미널 출력 읽기 시 인코딩 주의
- **경로 구분자**: Windows 백슬래시(`\\`) 이스케이프 필요 → 포워드 슬래시(`/`) 또는 raw string 사용
- **Python 버전**: python3.11과 python3.14 공존 시 venv 경로 확인 필수 (`/c/Users/kho/.hermes/hermes-agent/venv/Scripts/python.exe`)
- **⚠️ CRITICAL: System Python 3.14 FAILS with numpy C-extension error** — ALWAYS use Hermes venv Python (`/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`) for any script using yfinance/pandas/numpy. See `references/windows-python-env.md`.

### Cron Job Integration Notes (from 2026-08-18 session)

### Integrated Pipeline Cron Job Configuration
- **Job ID**: `abb99fffa684`
- **Schedule**: `30 9 * * *` (09:30 KST daily)
- **Skills**: `stock-analysis,technical-trading,hermes-stock-pipeline`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`)
- **Delivery**: `origin,telegram:6723387878`
- **Target tickers (5 core for technical)**: 삼성전자(005930), NVDA, 우리로(046970), SKC(011790), TIGER K방산&우주(453830)

### Intraday 30-Minute Monitoring Cron Job (from 2026-08-19 session, verified 2026-08-20)
- **Job ID**: `75de09c384ee`
- **Schedule**: `*/30 9-15 * * 1-5` (weekdays 09:00-15:00 KST, every 30 min)
- **Skills**: `technical-trading`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`) — **downgraded from 550B for cost efficiency**
- **Delivery**: `origin,telegram:6723387878`
- **Target tickers (17 active of 20)**: 9 KR + 8 US (see `references/intraday-30m-monitoring.md`)
- **Execution**: Local Python (venv) → data fetch, indicators, pattern detection → LLM only for signal summaries
- **Key learning**: Must use Hermes venv Python explicitly — system Python 3.14 fails with numpy C-extension error
- **First scheduled run (2026-08-20 15:01 KST)**: 17/20 tickers processed, 0 new signals, 12 tickers in Phase 2 (REBOUND), state persisted to `.signal_states.json`

### GitHub Actions Integration (2026-08-20 — Hybrid Architecture Validated)

**Problem**: GitHub Actions cron minimum interval is 1 hour — cannot run sub-hour (30-min) intraday monitoring reliably.

**Solution**: Hybrid architecture — GitHub Actions for daily batch, Local WSL for intraday:

| Layer | Jobs | Schedule | Why |
|-------|------|----------|-----|
| **GitHub Actions** | Daily technical signal snapshot (09:30 KST) | `30 0 * * *` (UTC) | Runs 24/7 free, PC independent |
| **Local WSL Cron** | Intraday 30-min monitoring | `*/30 9-15 * * 1-5` | Sub-hour cron, only when PC on |
| **Obsidian Sync** | Git pull reports | Manual or local cron | Reports committed to GitHub, pulled locally |

**GitHub Actions Job (`technical-signal-snapshot` in `.github/workflows/daily-stock.yml`)**:
- Runs once daily at 09:30 KST as a snapshot
- Uses `technical-trading` skill with NVIDIA NIM (550B primary, 70B fallback)
- Commits signal states to repo for local sync
- `continue-on-error: true` — doesn't block pipeline if intraday data unavailable

**Local WSL Cron (`75de09c384ee`)**:
- Runs every 30 min during market hours (09:00–15:30 KST, weekdays)
- Uses Hermes venv Python explicitly: `/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`
- Updates `.signal_states.json` locally, synced via Git

**Validated 2026-08-20**: Workflow file pushed to repo root `.github/workflows/daily-stock.yml`, GitHub Actions infrastructure installs successfully, Telegram test message delivered (message_id 30), model selection fixed (Google Gemini direct + NVIDIA NIM fallback instead of deprecated OpenRouter free model).
- **Workflow file MUST be at repo root `.github/workflows/`** — subdirectory paths ignored by GitHub Actions
- System Python 3.14 incompatible with numpy C-extensions → workflows must use Hermes venv Python explicitly
- `workflow_dispatch` with `job_type` choice input works for manual job selection

**See `references/github-actions-deployment-pitfalls.md` for complete deployment pitfalls checklist and hybrid architecture documentation.**

### Common Issues Observed
1. **Model provider drift**: When switching providers (OpenRouter → Google → NVIDIA), cron jobs need explicit model pinning via `cronjob` tool update
2. **Gateway must be running**: Telegram delivery fails if `hermes gateway` not running (`hermes gateway install && hermes gateway start`)
3. **Cron created after scheduled time**: If job created after 09:30, `next_run_at` = tomorrow — run manually today
4. **NVIDIA NIM model ID format**: Must use full ID (`nvidia/nemotron-3-ultra-550b-a55b`), not short name
5. **Python environment**: System Python 3.14 incompatible with venv numpy — cron commands must specify full venv Python path
6. **GitHub Actions sub-hour limitation**: Use hybrid approach — daily snapshot in cloud, intraday locally

### yfinance 30-minute Data Limitations (2026-08-19)
- **Period parameter preferred**: Use `period='30d'` instead of start/end dates for intraday — avoids timestamp timezone issues
- **Korean small caps/ETFs unsupported**: 우리로(046970), TIGER K방산&우주(453830), 토박스코리아(225460) return no 30m data
- **Working KR tickers (large cap)**: 005930, 000660, 011790, 252670, 373220, 006400, 035420, 035720, 005380
- **Working US tickers**: NVDA, NVDY, QQQ, TQQQ, AAPL, MSFT, GOOGL, AMZN
- **MultiIndex columns**: yfinance 1.6+ returns MultiIndex — must flatten with `df.columns.get_level_values(0)`

### Obsidian Storage for Technical Analysis
```
주식분석/
├── {종목명}/
│   └── {YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md
# Tags: #기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}
```

### Intraday Signal State Persistence
- **File**: `주식분석/.signal_states.json` — tracks phase, entry/stop/target prices, last signal time per ticker
- **Cooldown**: 60 minutes duplicate signal suppression via `last_signal_time`
- **Phases**: NONE(0) → FIRST_BOTTOM(1) → REBOUND(2) → SECOND_BOTTOM(3) → NECKLINE_WAIT(4) → BREAKOUT(5/BUY) → HOLDING(6)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08-16 | Initial technical trading skill with W-pattern double Bollinger Bands |
| 1.1.0 | 2026-08-18 | Added intraday 30-min monitoring, yfinance MultiIndex fix, pipeline integration |
| 1.2.0 | 2026-08-20 | First integrated pipeline run confirmed: 4/5 core tickers backtested, NVDA 100% win rate (9 trades, +44.45%), NVDA BUY signal active, 3 tickers unsupported by yfinance, system Python 3.14 numpy C-extension failure documented |
| 1.3.0 | 2026-08-20 | Second integrated pipeline run: NVDA BUY signal re-confirmed ($212.71 entry, $198.75 stop, $222.19 target, R:R 0.68), Samsung/SKC in Phase 1 (first bottom), KODEX 200 no pattern, Woori-lo (046970) skipped (21 days only), TIGER K방산우주 (453830) yfinance unsupported |
| 1.4.0 | 2026-08-20 | **GitHub Actions hybrid architecture validated**: (1) Workflow file at repo root `.github/workflows/daily-stock.yml` with 6 jobs. (2) `technical-signal-snapshot` job runs daily at 09:30 KST on cloud (PC-independent). (3) Local WSL cron `75de09c384ee` runs every 30 min 09:00-15:30 KST for intraday signals (PC-dependent). (4) Model selection fixed: Google Gemini direct (free) for fundamental, NVIDIA NIM 550B+70B fallback for technical. (5) `permissions: contents: write` required for git push from Actions. (6) Telegram delivery via appleboy/telegram-action confirmed (message_id 30). |

## References
- `references/pipeline-integration.md` — Pipeline integration with hermes-stock-pipeline
- `references/windows-yfinance-backtest.md` — Windows yfinance backtest patterns
- `references/yfinance-korea-stock-data.md` — Korean stock data via yfinance
- `references/automated-skill-hub-monitoring.md` — Shared monitoring pattern (in hermes-agent-operations)
- `references/verification-script-pattern.md` — Ad-hoc verification script template for backtest functions
- `references/yfinance-limitations.md` — Known yfinance limitations for Korean ETFs/small caps
- `references/yfinance-multiindex-fix.md` — yfinance MultiIndex column handling fix (2026-08-18)
- `references/intraday-30m-monitoring.md` — Intraday 30-minute signal monitoring pattern (2026-08-18)
- `references/session-2026-08-19-intraday-monitoring.md` — Setup & verification session
- `references/session-2026-08-20-intraday-cron-execution.md` — First scheduled cron execution results
- `references/session-2026-08-20-integrated-pipeline.md` — First integrated pipeline run details
- `references/session-2026-08-20-second-run.md` — Second integrated pipeline run details (2026-08-20)
## Scripts
- `scripts/run_daily_backtest.py` — 일일 백테스트 실행 스크립트 (cron job용, 핵심 5종목 대상)
- `scripts/verify_backtest.py` — 핵심 함수 검증 스크립트 (코드 변경 후 실행)
- `scripts/intraday_monitor.py` — 장중 30분봉 시그널 모니터링 (intraday cron용)
- `scripts/technical_signal_monitor.py` — 기술적 시그널 통합 모니터링

## Templates
- `templates/backtest_report_template.md` — 백테스트 리포트 마크다운 템플릿
- `templates/intraday_signal_template.md` — 장중 시그널 알림 템플릿

## 주의사항 & 한계
- **과적합 위험**: 과거 데이터에 맞춰 파라미터 최적화 시 미래 성과 보장 안됨
- **표본 부족**: 우리로 사례처럼 4.5년 1회 신호면 통계적 유의성 없음
- **시장 국면 의존**: 추세장/횡보장/하락장에서 성과 차이 큼
- **실전과 차이**: 슬리피지, 호가창 유동성, 세금(0.23%) 미반영 시 실제 수익률 더 낮음
- **확증 편향**: "맞는 경우만 기억" 방지 위해 전체 거래 내역 투명 공개 필수

## 확장 포인트
- 전략 2: RSI 다이버전스 + 볼린저밴드
- 전략 3: 이동평균선 정배열/역배열 눌림매매
- 전략 4: 거래량 급증 + 가격 돌파 (세력주 패턴)
- 멀티 타임프레임 분석 (일봉 + 주봉 + 월봉)
- 포트폴리오 레벨 백테스트 (여러 종목 동시 운용 시뮬레이션)