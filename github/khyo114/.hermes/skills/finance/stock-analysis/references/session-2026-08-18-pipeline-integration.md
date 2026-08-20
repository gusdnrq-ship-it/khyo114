# Session 2026-08-18 — Stock Analysis Pipeline Integration

## Cron Job Integration

### Job: `abb99fffa684` (Integrated Pipeline)
- **Schedule**: `30 9 * * *` (09:30 KST daily)
- **Skills**: `stock-analysis,technical-trading,hermes-stock-pipeline`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (provider: `nvidia`)

### Fundamental Analysis Targets (10 Tickers)
| Ticker | Name | Market | Notes |
|--------|------|--------|-------|
| 005930 | 삼성전자 | KOSPI | Core, 20.5% portfolio |
| 252670 | KODEX 200 | KOSPI | ETF, broad market |
| 453830 | TIGER K방산&우주 | KOSPI | Defense/space ETF |
| 225460 | 토박스코리아 | KOSDAQ | Small cap |
| 011790 | SKC | KOSPI | Semiconductor materials |
| NVDY | NVDY | NASDAQ | NVDA covered call ETF |
| NVDA | 엔비디아 | NASDAQ | Profitable holding |
| QQQ | QQQ | NASDAQ | Nasdaq 100 ETF |
| + 2 more | TBD | TBD | Need to complete 10 |

### Data Sources (Browser-Free)
1. **Naver Finance** (finance.naver.com) — `curl` + CSS selectors
2. **WiseReport/FnGuide** (wisereport.co.kr) — Financial statements, valuations
3. **Google News RSS** — news.google.com/rss/search?q={ticker}
4. **DART** (dart.fss.or.kr) — Official disclosures
5. **yfinance** — Price data for technical analysis (via technical-trading)

### Output Structure
```
주식분석/
├── YYYYMMDD_종합투자분석리포트.md          # 통합 리포트
├── 삼성전자/
│   └── YYYYMMDD_삼성전자.md
├── NVDA/
│   └── YYYYMMDD_엔비디아.md
└── ... (각 종목별)
```
**Tags**: `#주식분석 #종목코드 #섹터 #시장구분 #투자리포트`

## Model Configuration History (This Session)

| Attempt | Provider | Model | Result |
|---------|----------|-------|--------|
| 1 | OpenRouter | google/gemini-2.5-flash-lite | HTTP 402 (credits exhausted) |
| 2 | Google | gemini-2.5-flash | HTTP 429 (daily quota exceeded) |
| 3 | NVIDIA NIM | nvidia/nemotron-3-ultra-550b-a55b | ✅ Success |

**Fallback Chain** (config.yaml):
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

## Cron Job Model Pinning (Critical)
- **CLI limitation**: `hermes cron edit` lacks `--model/--provider` flags
- **Solution**: Use internal `cronjob` tool:
  ```python
  cronjob(action="update", job_id="abb99fffa684", 
          model={"model": "nvidia/nemotron-3-ultra-550b-a55b", "provider": "nvidia"})
  ```
- Takes effect immediately, no restart needed

## Gateway Setup for Telegram
```bash
# Windows Startup folder (persistent across WSL restarts)
hermes gateway install
hermes gateway start

# Verify
hermes gateway status
# → Gateway process running (PID: xxxx)
```

## Key Pitfalls Documented in stock-analysis Skill (Pitfall #0)
- Cron job checklist: model, provider, fallback_chain, API keys, Telegram bot
- Cron `execute_code` + `terminal` blocked in cron context
- Windows browser timeout/encoding issues
- Korean finance site CP949 encoding
- ETF/small cap data gaps in WiseReport
- Config drift error → explicit pinning required
- OpenRouter HTTP 402 / Google HTTP 429 quota limits

## Next Verification (2026-08-19)
- [ ] 09:30 cron fires automatically
- [ ] 10 tickers processed (need to add 2 more)
- [ ] No quota/quota errors with NVIDIA model
- [ ] Obsidian files created with correct tags
- [ ] Telegram summary received
- [ ] Gateway stays running overnight