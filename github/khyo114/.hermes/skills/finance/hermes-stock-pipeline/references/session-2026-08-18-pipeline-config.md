# Session 2026-08-18 — Integrated Pipeline Cron Configuration

## Cron Job Details

### Job: Integrated Stock Analysis Pipeline (Fundamental + Technical)
- **Job ID**: `abb99fffa684`
- **Name**: `통합 주식분석 파이프라인 (펀더멘털 + 기술적)`
- **Schedule**: `30 9 * * *` (09:30 KST daily)
- **Skills**: `stock-analysis,technical-trading,hermes-stock-pipeline`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`)
- **Delivery**: `origin,telegram:6723387878`
- **State**: Active, scheduled

### Job: Skill Hub Monitoring
- **Job ID**: `e39f4e13b494`
- **Name**: `Hermes 스킬 허브 자동 모니터링 & 평가`
- **Schedule**: `0 10 * * *` (10:00 KST daily)
- **Skills**: `hermes-agent-skill-authoring,requesting-code-review,hermes-agent`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`)
- **Delivery**: `origin,telegram:6723387878`
- **State**: Active, scheduled

## Execution Flow (Integrated Pipeline)

### 1단계: 펀더멘털 분석 (stock-analysis)
**대상 10종목**:
- 국내: 삼성전자(005930), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), SKC(011790)
- 해외: NVDY, NVDA, QQQ, (나머지 2개 추후 추가)

**출력**: `주식분석/{종목명}/{YYYYMMDD}_{종목명}.md` + 종합 리포트

### 2단계: 기술적 분석 (technical-trading)
**핵심 5종목**:
- 삼성전자(005930), NVDA, 우리로(046970), SKC(011790), TIGER K방산&우주(453830)

**전략**: 쌍굴파기 이중 볼린저밴드 (BB 20,2 + BB 20,1)
**출력**: `주식분석/{종목명}/{YYYYMMDD}_{종목명}_백테스트_쌍굴파기.md`
**태그**: `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기 #{종목코드}`

### 3단계: 통합 알림 (Telegram)
- 펀더멘털 요약 (종목별 핵심 지표, 뉴스, 리스크)
- 기술적 요약 (시그널 여부, 진입가/손절가/목표가, 리스크 레벨)
- Obsidian 저장 경로
- 실행 시간·소요 시간·에러 여부

## Model Configuration Rationale

| Provider | Model | Status | Reason |
|----------|-------|--------|--------|
| Google | gemini-2.5-flash | ❌ Quota exhausted (HTTP 429) | Free tier daily limit |
| OpenRouter | google/gemini-2.5-flash-lite | ❌ Credits exhausted (HTTP 402) | Free credits used up |
| NVIDIA NIM | nvidia/nemotron-3-ultra-550b-a55b | ✅ Working | NVIDIA_API_KEY available, generous free tier |

**Fallback chain in config.yaml**:
```yaml
model:
  default: google/gemini-2.5-flash
  provider: google
  fallback_chain:
    - provider: openrouter
      model: google/gemini-2.5-flash-lite
    - provider: nvidia
      model: nvidia/nemotron-3-ultra-550b-a55b
    - provider: google
      model: gemini-2.5-pro
```

## Gateway Setup (WSL)

```bash
# Windows Startup folder method (survives reboot)
hermes gateway install
hermes gateway start

# Verify
hermes gateway status
# → Gateway process running (PID: xxxx)
```

## Obsidian Storage Structure

```
주식분석/
├── YYYYMMDD_종합투자분석리포트.md          # 통합 리포트 (펀더멘털 + 기술적)
├── 삼성전자/
│   ├── YYYYMMDD_삼성전자.md               # 펀더멘털
│   └── YYYYMMDD_삼성전자_백테스트_쌍굴파기.md  # 기술적
├── NVDA/
│   ├── YYYYMMDD_엔비디아.md
│   └── YYYYMMDD_엔비디아_백테스트_쌍굴파기.md
├── 우리로/
│   ├── YYYYMMDD_우리로.md
│   └── YYYYMMDD_우리로_백테스트_쌍굴파기.md
└── ... (각 종목별 폴더)
```

**Tags**: `#주식분석 #종목코드 #섹터 #시장구분 #투자리포트` + `#기술적분석 #백테스트 #볼린저밴드 #쌍굴파기`

## Cron Job Management Commands

```bash
# List all jobs
hermes cron list

# Run manually (today's missed run)
cronjob(action="run", job_id="abb99fffa684")
cronjob(action="run", job_id="e39f4e13b494")

# Pause old single-analysis job
cronjob(action="pause", job_id="e70a7a1f1729")

# Update model pinning
cronjob(action="update", job_id="abb99fffa684", model={"model": "nvidia/nemotron-3-ultra-550b-a55b", "provider": "nvidia"})
```

## Verification Checklist for Next Run (2026-08-19)

- [ ] 09:30 — Integrated pipeline fires automatically
- [ ] 10:00 — Skill hub monitoring fires automatically
- [ ] Telegram messages received for both
- [ ] Obsidian files created in correct paths
- [ ] No model drift / quota errors
- [ ] Gateway stays running overnight