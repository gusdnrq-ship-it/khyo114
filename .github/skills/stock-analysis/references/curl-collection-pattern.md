# curl 기반 데이터 수집 패턴 (이 세션 검증��)

## 개요
`web_search`/`web_extract` 도구가 없는 환경에서 `terminal` + `curl`로 정적 HTML/XML을 직접 수집하여 파싱하는 패턴.

## 작동 확인된 소스별 curl 명령어

### 1. 네이버 금�� (finance.naver.com)
```bash
# 종목 뉴스 (페이지네이션)
curl -s -L --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7" \
  "https://finance.naver.com/item/news.naver?code={종목코드}&page=1" > naver_news_{종목코드}_p1.html

# 메인 페이지 (시세, 기본정보)
curl ... "https://finance.naver.com/item/main.naver?code={종목코드}" > naver_main_{종목코드}.html
```

### 2. 와이즈리포트 / FnGuide (navercomp.wisereport.co.kr)
```bash
# 기업개요
curl ... "https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={종목코드}" > wisereport_company_{종목코드}.html

# ����류에이션/투자지표
curl ... "https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx?cmp_cd={종목코드}" > wisereport_valuation_{종목코드}.html

# 재무분석
curl ... "https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx?cmp_cd={종목코드}" > wisereport_financial_{종목코드}.html

# 컨센서스
curl ... "https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd={종목코드}" > wisereport_consensus_{종목코드}.html
```

### 3. Google News RSS (브라우저 차단 우회)
```bash
curl -s -L --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7" \
  "https://news.google.com/rss/search?q={URL인코딩된검색어}&hl=ko&gl=KR&ceid=KR:ko" > google_news_{종목코드}.xml
```

## 파싱 전략 (BeautifulSoup + regex)

### 네이버 금융 메인 - 시세 정보 (검증됨)
- **첫 번째 `<dl class="blind">`**: 종목 시세 정보 (현재가, 전일대비, 시가/고가/저가, 거래량/거래대금)
  - `<dd>` 텍스트에서 키워드 매칭: "현재가", "전일대비", "전일가", "시가", "고가", "저가", "거래량", "거래대금"
  - 예: `"현재가 274,500 전일대비 상승 6,500 플러스 2.43 퍼센트"` → split 후 파싱
- **두 번째 `<dl class="blind">` (rate_info 내부)**: 오늘의 시세, 등락폭, 등락률
- **주요 시세 테이블** (`<table class="no_info">` 등):
  - 52주 최고/최저: `<th>`에 "52주최고/최저" 포함
  - PER/PBR: `<th>`에 "PER(배)", "PBR(배)" 포함 → `<td><em><span class="blind">` 값 추출
  - 시가배당률: `<th>`에 "시가배당률(%)" 포함
  - 외국인비율: `<th>`에 "외국인비율(%)" 또는 "외국인소진율" 포함
  - 시가총액: `<th>`에 "시가총액(억)" 포함

### 와이즈리포트 밸류에이션/투자지표 (검증됨)
- **상단 `<table class="cmp-table">` 내 `<dl>` 구조**:
  - `<dt>` 텍스트에 지표명, `<b class="num">`에 수치
  - EPS, BPS, PER, 업종PER, PBR, 현금배당수익률 직접 추출 가능
  - 네이버 금융보다 안정적으로 핵심 지표 확보 가능

### 와이즈리포트 기업개요 (`class="gHead"` 테이블)
- `<th>`/`<td>` 쌍에서 기업개요(대표이사, 본사주소, 홈페이지, 설립일, 상장일, 종업원수)
- 재무하이라이트(매출액, 영업이익, 당기순이익, 자산총계, 자본총계, 부채총계)

### 와이즈리포트 재무분석
- 테이블에서 수익성(ROE, ROA, 영업이익률, 순이익률), 안정성(부채비율, 유동비율), 성장성(매출액증가율, 영업이익증가율) 지표 추출

### 네이버 뉴스
- `<table class="type5">` 내 `<td class="title"><a>` 구조
- 제목, 링크, 날짜(`<td class="info">`) 추출

### Google News RSS
- `<item>` 내 `<title>`, `<link>`, `<pubDate>` 추출
- CDATA 섹션 처리 필요

## ⚠️ 인코딩 폴백 패턴 (필수 - 2026-08-16 검증)
네이버 금융, 와이즈리포트 등 국내 금융 사이트는 CP949(EUC-KR) 인코딩으로 응답할 수 있음.
파일 읽기 시 반드시 폴백 처리:

```python
def read_html_with_fallback(filepath):
    """UTF-8 실패 시 CP949로 재시도"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='cp949') as f:
            return f.read()

# 사용 예
html = read_html_with_fallback(filepath)
soup = BeautifulSoup(html, 'html.parser')
```

## ⚠️ ETF/소형주 와이즈리포트 데이터 부재 처리
- ETF(KODEX, TIGER 등) 및 시가총액 작은 종목: 와이즈리포트 기업개요/재무분석/밸류에이션 페이지가 138 bytes 빈 HTML 반환
- **대응**: 
  - 파일 크기 체크로 빈 페이지 감지 (`if len(html) < 500: return {}`)
  - 네이버 금융 메인 페이지 시세 테이블에서 PER, PBR, 시가배당률, 시가총액 등 기본 지표 보완
  - 밸류에이션 페이지만 일부 지표 제공 가능성 있어 시도하되, 실패 시 우아하게 건너뛰기

## 주의사항
- 네이버 금융 메인 페이지: 현재가 등 핵심 시세는 JavaScript로 동적 렌더링 → 정적 HTML에는 플레이스홀더만 있음
  - **해결**: 첫 번째/두 번째 `<dl class="blind">`에서 텍스트 형태로 실제 값 포함됨 (위 파싱 전략 참조)
- 와이즈리포트: 일부 구간 동적 렌더링 → 정적 HTML 파싱으로 커버 가능한 범위에서 추출
- 요청 간 1~2초 간격 권장 (IP 차단 방지)
- `charset=utf-8` 명시 필수 (Windows 환경 인코딩 이슈 방지)

## 이 세션에서 수집한 종목 (2026-08-15)
| 종목 | 코드 | 시장 | 수집 파일 |
|------|------|------|-----------|
| 삼성전자 | 005930 | 국내 | naver_main, naver_news(p1-3), wisereport_company/valuation/financial/consensus |
| KODEX 200 | 252670 | 국내 | naver_main, naver_news(p1), wisereport_company/valuation |
| TIGER K방산&우주 | 453830 | 국내 | naver_main, naver_news(p1), wisereport_company/valuation |
| 토박스코리아 | 225460 | 국내 | naver_main, naver_news(p1) |
| SKC | 011790 | 국내 | naver_main, naver_news(p1), wisereport_company/valuation |
| 대우건설 | 047040 | 국내 | naver_main, naver_news(p1), wisereport_company/valuation |
| NVDY | NVDY | 해외 | google_news_rss |
| 엔비디아 | NVDA | 해외 | google_news_rss |
| QQQ | QQQ | 해외 | google_news_rss |
| SPY | SPY | 해외 | google_news_rss |

## 검증된 파싱 코드 스니펫 (재사용용)
```python
# 네이버 메인 - 첫 번째 blind dl 파싱
blind_dl = soup.find('dl', class_='blind')
for dd in blind_dl.find_all('dd'):
    text = dd.get_text(strip=True)
    if '현재가' in text:
        parts = text.split()
        for i, part in enumerate(parts):
            if part == '현재가' and i+1 < len(parts):
                result['현재가'] = parts[i+1].replace(',', '')

# 와이즈리포트 밸류에이션 - cmp-table dl 파싱
cmp_table = soup.find('table', class_='cmp-table')
for dt in cmp_table.find_all('dt'):
    dt_text = dt.get_text(strip=True)
    b_tag = dt.find('b', class_='num')
    if b_tag:
        val = b_tag.get_text(strip=True)
        if 'PER' in dt_text and '업종' not in dt_text:
            result['PER'] = val
```