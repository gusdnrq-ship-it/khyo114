# Daily News Filtering Cron Job Pattern (2026-08-20)

## Overview
Automated daily news/filing filtering for 92 holdings (49 Korean + 43 US) executed at 07:00 KST via Hermes cron.

## Working Data Sources (Validated 2026-08-20)

### Korean Stocks (49 tickers)
- **Google News RSS**: `https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko`
  - Query: `삼성전자 OR SK하이닉스 OR 토박스코리아 OR 우리로 OR KODEX OR TIGER`
  - Returns 30+ articles from 조선일보, 한겨레, 연합뉴스, 머니투데이, 한국경제, 인베스트조선, etc.
  - Captures: 주주환원, 자사주소각, 실적, 계약, 신제품, 임단협 news

### US Stocks (43 tickers)
- **Yahoo Finance RSS**: `https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&region=US&lang=en-US`
  - Works for: NVDA, AAPL, MSFT, TSLA, QQQ, TQQQ, AMZN, GOOGL, META, etc.
  - Returns 15-20 articles per ticker from Motley Fool, Yahoo Finance, The Street, Stocktwits, Quartz, Benzinga
  - Captures: earnings guidance, price targets, product launches, macro analysis

### Failed/Blocked Sources
- Naver Finance: JavaScript-rendered, blocks automated access
- Daum Finance: 403 Forbidden
- OpenDART API: Requires registered auth key (demo key invalid)
- Google News RSS for US tickers: Returns empty (region/language restrictions)

## Ticker Matching Logic
```python
# 92 holdings hardcoded in script
kr_holdings = {"005930": "삼성전자", "000660": "SK하이닉스", ...}  # 49 total
us_holdings = {"NVDA": "NVIDIA", "AAPL": "Apple", ...}  # 43 total

# Matching: RSS item title/content contains ticker code or company name
# Korean: 6-digit code + name mapping
# US: Ticker symbol uppercase matching
```

## Scoring & Classification
| Factor | Weight |
|--------|--------|
| Source type (DART/공시 > 증권사 리포트 > 일반 뉴스) | 30% |
| Keyword matches (계약/수주/실적/배당/자사주/소각/급등/흑자전환) | 25% |
| Recency (recent 6 hours) | 15% |
| Broker report presence | 15% |
| Volume indicators (sidecar, 상한가) | 15% |

**Classification thresholds:**
- ≥30: 긍정
- 15-29: 중립
- 0-14: 참고
- <0: 부정

## Output Structure
**Obsidian path**: `주식분석/뉴스/{YYYYMMDD}_내종목뉴스.md`
**Tags**: `#뉴스 #공시 #DART #내보유종목`

**Report sections:**
1. 📈 긍정 신호 (N건) - with score, keywords, source link
2. ⚖️ 중립/참고 (N건)
3. 📉 부정/리스크 (N건)
4. 📊 요약 통계

## Telegram Notification Format
```
📰 [일일 뉴스] {YYYY-MM-DD} 내 종목 92개 중 {matched}건 매칭
✅ 긍정: {top_positive_names} 등 {pos_count}건
⚠️ 리스크: {top_negative_names} 등 {neg_count}건
📄 상세: 주식분석/뉴스/{YYYYMMDD}_내종목뉴스.md
```

## Cron Job Setup
```bash
hermes cron create "0 7 * * *" \
  "뉴스/공시 필터링 → 내 92종목만 추출 — 매일 07:00 KST

## 목적
DART 공시 + 네이버/다음 금융 뉴스 + 증권사 리포트에서 **내 보유 92종목(국내 49 + 해외 43) 티커 매칭** → 일일 \"내 종목 뉴스만\" 리포트 생성 → Obsidian + Telegram

## 내 보유 종목 티커 리스트 (하드코딩)
**국내 49개**: 005930, 000660, 011790, 046970, 252670, 453830, 225460, 373220, 006400, 035420, 035720, 005380, 051910, 005490, 068270, 096770, 207940, 012330, 017670, 033780, 009830, 010130, 024110, 032830, 034220, 047810, 058470, 066570, 091990, 105560, 138930, 145020, 161390, 192820, 214150, 214450, 247540, 251270, 267250, 285130, 293490, 302440, 316140, 326030, 340210, 352820, 357780, 365340
**해외 43개**: NVDA, NVDY, QQQ, TQQQ, AAPL, MSFT, GOOGL, AMZN, META, TSLA, AVGO, AMD, INTC, CRM, ORCL, ADBE, NFLX, CSCO, PEP, COST, TMUS, V, MA, JPM, BAC, WMT, HD, PG, JNJ, UNH, MRK, ABBV, PFE, TMO, DHR, ABT, LLY, BMY, AMGN, GILD, ISRG

## 데이터 소스 (브라우저 미사용, 무료 API/RSS)
### 1. Google News RSS (한국)
- https://news.google.com/rss/search?q=삼성전자+OR+SK하이닉스+OR+...&hl=ko&gl=KR&ceid=KR:ko

### 2. Yahoo Finance RSS (미국)
- https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA&region=US&lang=en-US
- Repeat for each US ticker

## 실행 로직
1. 원본 수집: web_extract로 각 소스에서 최근 24시간 데이터 수집
2. 티커 매칭: 로컬 Python으로 본문에서 티커 패턴 추출 → 92개 리스트와 교집합
3. 중요도 스코어링: 로컬 로직 (공시유형 30% + 키워드 25% + 조회수 15% + 리포트여부 15% + 최신성 15%)
4. LLM 요약: 매칭된 기사만, 종목당 1회 (~300 토큰)
5. 일일 리포트 생성: Obsidian 저장
6. Telegram 알림: 핵심만 3줄 요약

## 모델 고정
- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b" \
  --skill hermes-stock-pipeline \
  --name "일일 뉴스 필터링 (92종목)" \
  --model nvidia/nemotron-3-ultra-550b-a55b \
  --provider nvidia \
  --deliver origin,telegram:6723387878
```

## Results (2026-08-20 First Run)
- **Total collected**: 15 articles matched from 92 holdings
- **Positive**: 8 (SK하이닉스 40조 자사주소각, 삼성전자 주주환원/파운드리단가인상, NVDA 목표가상향, TSLA 사이버캡)
- **Neutral**: 5 (삼성전자 갤S26, AAPL 메가캡/AI지출, MSFT 백로그, QQQ ETF)
- **Negative**: 2 (MSFT 중국윈도우이탈, NVDA 가이던스하회)
- **Obsidian saved**: `주식분석/뉴스/20260820_내종목뉴스.md`
- **Telegram delivered**: ✅

## Key Learnings
1. **RSS > HTML scraping** for reliability — Google News RSS and Yahoo Finance RSS are stable, free, no auth needed
2. **Google News RSS Korean query** returns rich multi-source coverage (10+ Korean outlets)
3. **Yahoo Finance RSS per-ticker** requires 43 separate calls but each returns 15+ articles
4. **Local scoring + LLM summary only for matched items** minimizes token usage
5. **Hardcoded 92 tickers** in script avoids external dependency; update quarterly
6. **07:00 KST timing** catches pre-market Korean news + overnight US news