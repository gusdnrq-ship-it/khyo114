# Korean Finance Data Sources & Parsing Patterns

## Verified Working Sources (2026-08-16)

| Source | URL Pattern | Data Type | Encoding | Notes |
|--------|-------------|-----------|----------|-------|
| **네이버 금융 메인** | `https://finance.naver.com/item/main.naver?code={code}` | 시세, 기본정보 | CP949 | `dl.blind` 파싱 |
| **네이버 금융 뉴스** | `https://finance.naver.com/item/news.naver?code={code}&page=1` | 종목 뉴스 | CP949 | `table.type5` 파싱 |
| **와이즈리포트 기업개요** | `https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}` | 기업개요 | CP949 | `table.gHead` 파싱 |
| **와이즈리포트 밸류에이션** | `https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx?cmp_cd={code}` | PER, PBR, EPS, BPS 등 | CP949 | `table.cmp-table` 파싱 |
| **와이즈리포트 재무분석** | `https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx?cmp_cd={code}` | ROE, ROA, 부채비율 등 | CP949 | 테이블 파싱 |
| **와이즈리포트 컨센서스** | `https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd={code}` | 목표가, 투자의견 | CP949 | 제한적 |
| **Google News RSS** | `https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko` | 최신 뉴스 | UTF-8 | XML 파싱 |

## Curl Collection Patterns

### Basic Template

```bash
curl -s -L --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7" \
  "URL" > output.html
```

### With Sleep (Anti-blocking)

```bash
curl ... "URL1" > file1.html
sleep 2
curl ... "URL2" > file2.html
sleep 2
```

### Windows PowerShell (Invoke-WebRequest)

```powershell
Invoke-WebRequest -Uri "URL" -Headers @{
    "User-Agent" = "Mozilla/5.0..."
    "Accept-Language" = "ko-KR,ko;q=0.9"
} -OutFile "output.html"
```

## Parsing Selectors (BeautifulSoup)

### 네이버 금융 메인 (`dl.blind`)

```python
blind_dls = soup.find_all('dl', class_='blind')
# first_dl: 현재가, 전일대비, 시가/고가/저가, 거래량/거래대금
# second_dl: 등락률
```

### 네이버 금융 시세 테이블 (`table`)

```python
tables = soup.find_all('table')
for table in tables:
    for th in table.find_all('th'):
        th_text = th.get_text(strip=True)
        td = th.find_next_sibling('td')
        # blind span 또는 em 태그에서 값 추출
```

### 네이버 뉴스 (`table.type5`)

```python
table = soup.find('table', class_='type5')
rows = table.find_all('tr')
for row in rows:
    title_td = row.find('td', class_='title')
    info_td = row.find('td', class_='info')
    # a 태그에서 제목/링크, info에서 날짜
```

### 와이즈리포트 기업개요 (`table.gHead`)

```python
tables = soup.find_all('table', class_='gHead')
for table in tables:
    for row in table.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        # 대표이사, 본사, 홈페이지, 설립일, 상장일, 종업원수
```

### 와이즈리포트 밸류에이션 (`table.cmp-table`)

```python
tables = soup.find_all('table', class_='cmp-table')
for table in tables:
    dts = table.find_all('dt')
    for dt in dts:
        dt_text = dt.get_text(strip=True)
        b_tag = dt.find('b', class_='num')
        # EPS, BPS, PER, PBR, 현금배당수익률, EV/EBITDA
```

### Google News RSS (XML)

```python
soup = BeautifulSoup(xml, 'xml')
items = soup.find_all('item')
for item in items[:15]:
    title = item.find('title').get_text(strip=True)
    link = item.find('link').get_text(strip=True)
    pub_date = item.find('pubDate').get_text(strip=True)
    desc = item.find('description').get_text(strip=True)
```

## ETF/소형주 처리 주의사항

| 종목 유형 | 와이즈리포트 데이터 | 대체 수집 방안 |
|-----------|---------------------|----------------|
| ETF (KODEX, TIGER 등) | 기업개요/밸류에이션/재무분석 빈 페이지 | 네이버 금융 시세표에서 PER, PBR, 시가배당률, 시가총액 수집 |
| 소형주/관리종목 | 일부 데이터 없음 | 네이버 금융 기본정보 + 뉴스 위주 |

## User-Agent Rotation (Anti-blocking)

```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

import random
headers = {"User-Agent": random.choice(USER_AGENTS)}
```

## Rate Limiting

```python
import time
import random

# 요청 간 1-3초 랜덤 대기
time.sleep(random.uniform(1, 3))
```

## ETF 전용 지표 수집

| 지표 | 수집 소스 | 비고 |
|------|-----------|------|
| NAV (순자산가치) | 자산운용사 홈페이지 | 일별 공시 |
| 추적오차 | 자산운용사 월보 | 월간 |
| 운용보수 | 투자설명서/홈페이지 | 연간 |
| 분배금 | 공시/홈페이지 | 분기/반기 |
| 구성종목 | ETF 구성종목 공시 | 일별/주간 |