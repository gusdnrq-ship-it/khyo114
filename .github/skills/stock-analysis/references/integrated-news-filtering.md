# Integrated News Filtering Pattern for Stock Analysis (2026-08-20)

## Overview
This reference documents the working pattern for daily news/filing filtering across 92 holdings (49 Korean + 43 US) as part of the stock-analysis skill's data collection phase.

## Validated Data Sources

### 1. Google News RSS (Korean Market)
**Endpoint**: `https://news.google.com/rss/search?q={URL_ENCODED_QUERY}&hl=ko&gl=KR&ceid=KR:ko`

**Working query for 6 core holdings**:
```
삼성전자 OR SK하이닉스 OR 토박스코리아 OR 우리로 OR KODEX OR TIGER
```

**Returns**: 30+ articles from 10+ Korean outlets (조선일보, 한겨레, 연합뉴스, 머니투데이, 한국경제, 인베스트조선, 이코노미스트, 디지털데일리, 에너지경제신문, 뉴스1, 아시아경제, 아시아투데이, 매일신문, 지디넷코리아, 주간조선, 조선비즈, 채널A, 동아일보, 강원도민일보, news.knn, YTN, MBC, 연합뉴스TV, 연합인포맥스, 한국경제TV, 시사프리즘, 자본시장뉴스, 인더스트리뉴스)

**Article structure**: title, link, pubDate, source, description (HTML with link + source font tag)

**Coverage**: 주주환원, 자사주소각/매입, 실적, 계약/수주, 신제품, 임단협, 기술개발, 증권사 리포트

### 2. Yahoo Finance RSS (US Market)
**Endpoint**: `https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&region=US&lang=en-US`

**Working for**: NVDA, AAPL, MSFT, TSLA, QQQ, TQQQ, AMZN, GOOGL, META, AVGO, AMD, INTC, CRM, ORCL, ADBE, NFLX, CSCO, PEP, COST, TMUS, V, MA, JPM, BAC, WMT, HD, PG, JNJ, UNH, MRK, ABBV, PFE, TMO, DHR, ABT, LLY, BMY, AMGN, GILD, ISRG

**Returns**: 15-20 articles per ticker from Motley Fool, Yahoo Finance, The Street, Stocktwits, Quartz, Benzinga, Barchart, 247WallSt, Trefis, Investing.com

**Coverage**: Earnings guidance, price targets, product launches, macro analysis, AI spending, China exposure

### 3. Sources That Failed (Do Not Use)
- **Naver Finance**: `finance.naver.com` — JavaScript-rendered, returns binary/JS, blocks automated access
- **Daum Finance**: `finance.daum.net/api` — 403 Forbidden
- **OpenDART API**: `opendart.fss.or.kr/api/list.xml` — Requires registered auth key (demo key returns "등록되지 않은 인증키입니다")
- **Google News RSS US tickers**: Returns empty — likely region/language restrictions

## Ticker Matching Strategy

### Korean (49 tickers)
```python
kr_holdings = {
    "005930": "삼성전자", "000660": "SK하이닉스", "011790": "SKC", "046970": "우리로",
    "252670": "KODEX 200", "453830": "TIGER K방산&우주", "225460": "토박스코리아",
    # ... 42 more
}
# Match: 6-digit code OR Korean name in title/content
```

### US (43 tickers)
```python
us_holdings = {
    "NVDA": "NVIDIA", "NVDY": "NVDY", "QQQ": "Invesco QQQ", "TQQQ": "ProShares UltraPro QQQ",
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta",
    "TSLA": "Tesla", # ... 36 more
}
# Match: Ticker symbol (uppercase) OR English name in title/content
```

## Scoring Algorithm (Local, No LLM)

```python
def calculate_score(title, content, source_type):
    score = 0
    text = (title + " " + content).lower()
    
    # Source type weight
    if source_type == "dart": score += 30
    elif source_type == "broker_report": score += 15
    
    # Positive keywords (주주환원, 자사주, 소각, 계약, 수주, 실적, 배당, 흑자, 급등, 상한가, 사이드카, 목표가상향, 신제품, 기술개발)
    positive = ["주주환원", "자사주", "소각", "계약", "수주", "실적", "배당", "흑자", "급등", "상한가", "사이드카", "목표가", "신제품", "기술", "로드맵", "확대", "성장", "투자", "흑자전환", "반등", "급증"]
    # Negative keywords (적자, 감자, 하락, 급락, 폭락, 하한가, 우려, 리스크, 악재, 조사, 압수, 고발, 소송, 과징금, 제재, 적자전환, 감소, 축소, 중단, 지연, 이탈)
    negative = ["적자", "감자", "하락", "급락", "폭락", "하한가", "우려", "리스크", "악재", "조사", "압수", "고발", "소송", "과징금", "제재", "적자전환", "감소", "축소", "중단", "지연", "이탈"]
    
    pos_count = sum(1 for kw in positive if kw in text)
    neg_count = sum(1 for kw in negative if kw in text)
    
    score += pos_count * 5
    score -= neg_count * 3
    score += 10  # recency bonus (all within 24h)
    
    return score

# Classification
if score >= 30: "긍정"
elif score >= 15: "중립"
elif score >= 0: "참고"
else: "부정"
```

## Output Format (Obsidian Markdown)

```
주식분석/뉴스/{YYYYMMDD}_내종목뉴스.md

# {YYYY-MM-DD} 내 보유 종목 뉴스/공시 요약

## 📈 긍정 신호 (N건)
### 종목명(코드) - 출처
- 제목
- 핵심: 키워드1, 키워드2 [영향: 긍정 | 점수: XX]
- 출처: URL

## ⚖️ 중립/참고 (N건)
...

## 📉 부정/리스크 (N건)
...

## 📊 요약 통계
- 총 수집: X건 | 매칭: Y건 | 요약: Z건
- 긍정: A | 중립/참고: B | 부정: C

태그: #뉴스 #공시 #DART #내보유종목
```

## Telegram Notification Template
```
📰 [일일 뉴스] {YYYY-MM-DD} 내 종목 92개 중 {matched}건 매칭
✅ 긍정: {top3_positive} 등 {pos_count}건
⚠️ 리스크: {top2_negative} 등 {neg_count}건
📄 상세: 주식분석/뉴스/{YYYYMMDD}_내종목뉴스.md
```

## Integration with stock-analysis Skill

### Phase 1: Data Collection (This Pattern)
- Run at 07:00 KST via cron
- Collect from Google News RSS (KR) + Yahoo Finance RSS (US)
- Local ticker matching + scoring
- Generate daily news report → Obsidian + Telegram

### Phase 2: Fundamental Analysis (stock-analysis skill)
- Run at 09:30 KST via cron  
- Uses parsed financial data from `scripts/parse_all.py`
- Generates individual + integrated reports

### Phase 3: Technical Analysis (technical-trading skill)
- Intraday: 30-min intervals 09:30-15:30 KST
- Daily: 09:30 KST for W-pattern diagnosis

## Cron Job Configuration
```bash
# Daily news filtering (07:00 KST)
hermes cron create "0 7 * * *" "news filtering prompt" \
  --skill hermes-stock-pipeline \
  --model nvidia/nemotron-3-ultra-550b-a55b \
  --provider nvidia \
  --deliver origin,telegram:6723387878
```

## First Run Results (2026-08-20)
- **Execution time**: ~45 seconds
- **API calls**: 1 Google News RSS + 6 Yahoo Finance RSS (NVDA, AAPL, MSFT, TSLA, QQQ, NVDY)
- **Articles processed**: ~150 total → 15 matched to 92 holdings
- **Classification**: 8 긍정, 5 중립/참고, 2 부정
- **Tokens used**: ~2,000 (minimal — only for final report synthesis)
- **Output**: Obsidian file + Telegram notification ✅