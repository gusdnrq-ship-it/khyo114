# 통합 파이프라인 실행 패턴 (펀더멘털 + 기술적)

## 개요
매일 09:30 KST 크론 잡에서 **stock-analysis(펀더멘털)** → **technical-trading(기술적)** 순차 실행하여 종합 리포트 생성.

## 크론 잡 설정 (검증된 구성)

```bash
hermes cron create "30 9 * * *" \
  "통합 주식분석 파이프라인 실행 — 매일 09:30 KST

## 1단계: 펀더멘털 분석 (stock-analysis 스킬)
대상 10종목:
- 국내: 삼성전자(005930), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), SKC(011790)
- 해외: NVDY, NVDA, QQQ, (나머지 2개는 기존 설정 유지)

각 종목별로:
- 뉴스·공시·유튜브·전문가 의견·재무제표·계약 현황 수집
- 종합 투자 분석 리포트 생성
- 저장: 주식분석/{종목명}/{YYYYMMDD}_{종목명}.md (태그 포함)
- 통합 리포트: 주식분석/YYYYMMDD_종합투자분석리포트.md

## 2단계: 기술적 분석 (technical-trading 스킬)
핵심 종목 5개에 대해 **쌍굴파기 이중 볼린저밴드** 전략 백테스트 + 현재 시그널 진단:
- 삼성전자(005930) — 대장주, 유동성 풍부
- NVDA — 해외 반도체 대장주
- 우리로(046970) — 전략 원 검증 종목 (4.5년 1회 신호, 손실 기록)
- SKC(011790) — 2차전지 소재, 변동성 큼
- TIGER K방산&우주(453830) — 방산/우주 테마 ETF

각 종목별로:
1. yfinance로 최근 3년 일봉 데이터 수집 (브라우저 미사용)
2. BB(20,2) + BB(20,1) 지표 계산
3. W-패턴 탐지 → 백테스트 실행 (수수료 0.015%, 슬리피지 0.1%)
4. 현재 시그널 단계 진단 (1차 바닥/반등/2차 바닥/넥라인 대기/돌파 확인)
5. 결과 저장: 주식분석/{종목명}/{YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md
   태그: #기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}

## 3단계: 통합 알림 (Telegram)
- 펀더멘털 요약: 종목별 투자 의견(매수/보유/매도), 핵심 리스크/촉매
- 기술적 요약: 현재 시그널 여부, 진입가/손절가/목표가, 리스크 레벨
- Obsidian 저장 경로 안내
- 실행 시간·소요 시간·에러 여부 포함" \
  --skill stock-analysis,technical-trading,hermes-stock-pipeline \
  --name "통합 주식분석 파이프라인 (펀더멘털 + 기술적)" \
  --model google/gemini-2.5-flash-lite \
  --provider openrouter \
  --deliver origin,telegram:6723387878
```

## 모델/프로바이더 고정 (drift 방지)
```bash
# 크론 잡 생성 시 명시적 지정
hermes cron create "30 9 * * *" "프롬프트" \
  --model google/gemini-2.5-flash-lite \
  --provider openrouter \
  --name "작업명"

# 또는 기존 잡 수정
hermes cron edit <job_id> --model google/gemini-2.5-flash-lite --provider openrouter
```

## 실행 원칙
1. **브라우저 자동화 금지** — CAPTCHA/타임아웃 회피, `curl` + `yfinance`만 사용
2. **yfinance 가격 데이터** — FinanceDataReader 미작동 환경에서 유일한 대안
3. **Windows 경로** — 포워드 슬래시(`/`) 또는 raw string(`r"C:\..."`) 사용
4. **인코딩 강제** — `LANG=ko_KR.UTF-8`, `PYTHONIOENCODING=utf-8`
5. **에러 격리** — 개별 종목 실패 시 스킵하고 계속 진행, 마지막에 에러 요약

## Obsidian 저장 구조
```
주식분석/
├── YYYYMMDD_종합투자분석리포트.md          # 펀더멘털 통합
├── YYYYMMDD_기술적분석_요약.md             # 기술적 통합
├── YYYYMMDD_파이프라인_실행보고서.md       # 실행 메타데이터
├── 삼성전자/
│   ├── YYYYMMDD_삼성전자.md                  # 펀더멘털
│   └── YYYYMMDD_삼성전자_백테스트_쌍굴파기.md # 기술적
├── NVDA/
│   ├── YYYYMMDD_엔비디아.md
│   └── YYYYMMDD_엔비디아_백테스트_쌍굴파기.md
└── ... (각 종목별 폴더)
```

## 태그 규칙
- 펀더멘털: `#주식분석 #종목코드 #섹터 #시장구분 #투자리포트`
- 기술적: `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}`

## 검증된 크론 잡 ID (이 세션)
- **Job ID**: `abb99fffa684`
- **Schedule**: `30 9 * * *` (09:30 KST daily)
- **Skills**: `stock-analysis,technical-trading,hermes-stock-pipeline`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`)
- **Delivery**: `origin,telegram:6723387878`

## 일반적인 문제와 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| Model drift 에러 | 전역 설정 변경 시 unpinned 잡 차단 | `--model/--provider` 명시 또는 `cronjob` 툴로 핀 고정 |
| Telegram 미전송 | 게이트웨이 미실행 | `hermes gateway install && hermes gateway start` |
| yfinance 404 | 한국 ETF 미지원 | 네이버 금융 API로 대체 수집 |
| 데이터 기간 부족 | 소형주 yfinance 제한 | 네이버 금융 일봉 API 보완 |
| 중복 진입 신호 | 동일 진입일 중복 탐지 | `detect_w_pattern` 중복 제거 로직 추가 필요 |

## 차기 개선 사항
1. TIGER K방산우주 네이버 금융 API 대체 수집 구현
2. 우리로 장기 데이터 네이버 금융에서 보완
3. 중복 진입 방지 로직 `technical_backtest.py`에 추가
4. ETF 전용 지표(NAV, 추적오차, 운용보수) 수집 추가
5. Telegram 마크다운 테이블 → 일반 텍스트 변환 (렌더링 이슈 방지)