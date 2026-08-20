# 한국 금융 데이터 수집용 검증된 소스/RSS/선택자 목록

## 검증된 데이터 소스 (이 세션에서 작동 확인)

### 1. 네이버 금융 (finance.naver.com)
| 데이터 | URL 패턴 | 비고 |
|--------|----------|------|
| 종목 뉴스 | `https://finance.naver.com/item/news.naver?code={종목코드}&page=1` | 리스트형, 크롤링 용이 |
| 뉴스 상세 | `https://finance.naver.com/item/news_news.naver?code={종목코드}&page=1` | 상세 본문 포함 |
| 시세/기본정보 | `https://finance.naver.com/item/main.naver?code={종목코드}` | 현재가, 시가총액 등 |
| 재무제표 | `https://finance.naver.com/item/main.naver?code={종목코드}#financial` | 연간/분기 재무 |
| 주주현황 | `https://finance.naver.com/item/main.naver?code={종목코드}#stockholder` | 대주주, 기관/외국인 지분율 |
| 투자자별 매매동향 | `https://finance.naver.com/item/frgn.naver?code={종목코드}` | 외국인/기관 순매수량 |

### 2. 와이즈리포트 / FnGuide (navercomp.wisereport.co.kr)
| 데이터 | URL 패턴 | 비고 |
|--------|----------|------|
| 기업개요 | `https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={종목코드}` | 사업개요, 주요제품, 재무하이라이트 |
| 컨센서스 | `https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd={종목코드}` | 목표주가, 투자의견 |
| 밸류에이션/투자지표 | `https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx?cmp_cd={종목코드}` | PER, PBR, EPS, BPS, 배당수익률, EV/EBITDA (핵심 지표 안정적 추출) |
| 재무분석 | `https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx?cmp_cd={종목코드}` | 수익성, 안정성, 성장성 지표 |

### 3. 네이버 뉴스 (news.naver.com)
| 데이터 | URL 패턴 | 비고 |
|--------|----------|------|
| 종목별 뉴스 검색 | `https://news.naver.com/main/search.naver?query={종목명}&section=finance` | 최신순 정렬 가능 |
| 섹션별 뉴스 | `https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258` | 증권 섹션 |

### 4. Google News RSS (브라우저 차단 우회용, 해외 종목 필수)
```
# 국내 종목 (한글 검색)
https://news.google.com/rss/search?q={종목명}+주식&hl=ko&gl=KR&ceid=KR:ko

# 해외 종목 (영문 검색, 심볼 사용)
https://news.google.com/rss/search?q={심볼}+stock&hl=en&gl=US&ceid=US:en
```
- CAPTCHA 없음, 빠른 응답, 구조화된 XML 파싱 용이
- 해외 ETF/종목(NVDY, NVDA, QQQ, SPY 등) 뉴스 수집 시 필수

## 크롤링 시 필수 헤더
```bash
-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
-H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
-H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
```

## 작동 확인된 curl 명령어 (2026-08-15)
```bash
# 국내 종목 전체 수집 루프
for code in 005930 252670 453830 225460 011790 047040; do
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://finance.naver.com/item/main.naver?code=$code" > naver_main_${code}.html
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://finance.naver.com/item/news.naver?code=$code&page=1" > naver_news_${code}_p1.html
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=$code" > wisereport_company_${code}.html
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx?cmp_cd=$code" > wisereport_valuation_${code}.html
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx?cmp_cd=$code" > wisereport_financial_${code}.html
  sleep 2
done

# 해외 종목 Google News RSS
for symbol in NVDY NVDA QQQ SPY; do
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://news.google.com/rss/search?q=${symbol}+stock&hl=en&gl=US&ceid=US:en" > google_news_${symbol}.xml
  sleep 2
done
```

## ⚠️ 주의사항
- 네이버 금융: 과도한 요청 시 IP 차단 가능성 → 요청 간 1~2초 간격 권장
- 와이즈리포트: 동적 렌더링 일부 구간 존재 → curl로 정적 HTML 파싱 권장 (밸류에이션 페이지가 가장 안정적)
- 브라우저 네비게이션은 **최후의 수단**으로만 사용 (타임아웃/인코딩 이슈 빈번)
- ETF 종목(KODEX 200, TIGER 등)은 와이즈리포트 재무분석/기업개요가 빈 페이지(138 bytes) 반환될 수 있음 → 밸류에이션 페이지만 활용