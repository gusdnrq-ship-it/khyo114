# 내 보유종목 92개 뉴스 필터링 파이프라인 패턴

## 개요
자신이 보유한 92개 종목(국내 49개 + 해외 43개)에 대해 다중 소스에서 뉴스/공시 수집 → 내 종목만 필터링 → 중요도 평가 → 일일 리포트 생성 → Obsidian/Telegram 전달.

## 데이터 소스 및 수집 패턴

### 1. DART 공시 (Open API)
```python
# 단일 호출로 전체 종목 공시 조회 (페이지당 100건)
url = f"https://opendart.fss.or.kr/api/list.xml?crtfc_key={API_KEY}&page_count=100"
```
- **한계**: API 키 필요, 실시간성 낮음 (15분 지연), 빈 응답 빈번

### 2. 네이버 금융 뉴스 섹션 (news.naver.com/main/list.naver)
```bash
# 증권 섹션 (sid1=101, sid2=258)
curl -H "User-Agent: Mozilla/5.0..." \
  "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258"
```
- **특징**: 300+ 기사 한 번에 수집, UTF-8 인코딩, `n.news.naver.com/mnews/article/` 링크 패턴
- **파싱**: `BeautifulSoup`으로 모든 `a[href*="n.news.naver.com/mnews/article/"]` 추출

### 3. 네이버 뉴스 검색 (모바일 버전) - **핵심 수정**
```bash
# PC 버전은 403/복잡한 DOM → 모바일 버전 사용
curl -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)..." \
  "https://m.search.naver.com/search.naver?where=m_news&sm=mtb_jum&query={종목명}"
```
- **핵심**: iPhone User-Agent 필수, `ZZCBS7C_fwcZFi3Z` 클래스 컨테이너에서 기사 추출
- **파싱 대상**:
  - 제목: `a[data-heatmap-target=".title"]` → 텍스트 + `href`
  - 언론사: `sds-comps-profile-info-title-text` 클래스
  - 날짜: `sds-comps-text` 클래스 중 "시간/분/일/전" 포함 텍스트

### 4. Google News RSS (해외 종목) - **핵심 수정**
```bash
# 종목별 RSS 피드
curl "https://news.google.com/rss/search?q={티커}&hl=en-US&gl=US&ceid=US:en"
```
- **거짓 양성 방지**: `target_code` 파라미터로 티커 경계 매칭 필수
  - 매칭 패턴: `NVDA:`, `NVDA `, `(NVDA)`, `NVDA,`, `NVDA.`
  - NVDY 검색 시 NVDA 단독 언급 → NVDY 매칭 차단 로직 추가
- **파싱**: `lxml` 파서 사용 (XML 네임스페이스 처리)

### 5. 다음 금융 뉴스 (차단됨)
- 403 Forbidden 지속 → 현재 사용 불가

## 티커/종목명 매칭 로직 (`extract_tickers_from_text`)

```python
def extract_tickers_from_text(text):
    """텍스트에서 티커/종목명 추출 - 정교한 매칭"""
    found = set()
    text_lower = text.lower()
    
    for code, info in MY_HOLDINGS.items():
        if info['market'] == '해외':
            # 단어 경계 고려: 공백, 쉼표, 마침표, 괄호 등
            import re
            pattern = r'(^|[\s,\.\(\)\[\]\:\;])' + re.escape(code.lower()) + r'($|[\s,\.\(\)\[\]\:\;])'
            if re.search(pattern, text_lower):
                found.add(code)
        else:
            # 국내: 6자리 숫자 코드 직접 매칭
            if code in text:
                found.add(code)
        
        # 종목명 정확 매칭
        if info['name'] in text:
            found.add(code)
        
        # NVDY가 NVDA만 언급된 기사에 매칭되지 않게 차단
        if code == 'NVDY' and 'NVDY' not in text and 'YieldMax' not in text and 'NVDA' in text:
            if 'NVDY' in found:
                found.remove('NVDY')
    
    return found
```

## 영향도 분류 (키워드 휴리스틱)

```python
POSITIVE_KEYWORDS = [
    '흑자', '흑자전환', '매출증가', '영업이익', '호실적', '상향', '매수', '목표가상향',
    '실적호조', '확대', '진출', '계약', '수주', '돌파', '신고가', '배당', '자사주',
    '인수', '합병', '신제품', 'FDA', '승인', '특허', '독점', '독자', '세계최초',
    '1위', '최고', '사상최대'
]

NEGATIVE_KEYWORDS = [
    '적자', '적자전환', '매출감소', '영업적자', '감자', '상장폐지', '횡령', '배임',
    '소송패소', '과징금', '압수수색', '하향', '매도', '목표가하향', '실적부진',
    '축소', '철수', '손실', '부진', '우려', '리스크', '악재', '하락', '내림',
    '다운', '감소', '약세', '내려', '떨어', '부도', '파산', '조사', '제재'
]

def classify_impact(text):
    text_lower = text.lower()
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    
    if pos_count > neg_count:
        return '긍정'
    elif neg_count > pos_count:
        return '부정'
    return '중립'
```

## 파이프라인 실행 흐름

```python
def main():
    all_items = []
    
    # 1. 네이버 금융 뉴스 섹션 (공통)
    all_items.extend(parse_naver_section_news(naver_section_path))
    
    # 2. 국내 종목별 네이버 뉴스 검색 (모바일, 49개 종목)
    for code in domestic_codes:
        download_naver_search_mobile(code, name)  # 캐싱
        all_items.extend(parse_naver_search_news(path, code))
    
    # 3. 해외 종목별 Google News RSS (43개 종목)
    for code in foreign_codes:
        download_google_news_rss(code)  # 캐싱
        all_items.extend(parse_google_news_rss(path, code))
    
    # 4. 중복 제거 (링크 기준)
    unique_items = deduplicate_by_link(all_items)
    
    # 5. 내 종목 매칭 + 영향도 분류
    for item in unique_items:
        item['impact'] = classify_impact(item['title'] + ' ' + item.get('summary', ''))
        item['tickers'] = extract_tickers_from_text(item['title'] + ' ' + item.get('summary', ''))
    
    # 6. 내 종목만 필터링 + 상위 50건 선택
    my_items = [i for i in unique_items if i['tickers']]
    top_items = sorted(my_items, key=lambda x: IMPACT_PRIORITY[x['impact']])[:50]
    
    # 7. 마크다운 리포트 생성 + Telegram 포맷 출력
    generate_report(top_items)
```

## 주요 수정 이력 (이 세션)

| 문제 | 원인 | 해결 |
|------|------|------|
| 전체 기사가 '중립' 분류 | LLM 요약 미구현, 휴리스틱 부재 | 긍정/부정 키워드 사전 구축, 휴리스틱 분류 구현 |
| Google RSS NVDY→NVDA 오매칭 | 부분 문자열 매칭 | 티커 경계 매칭(공백/구두점) + NVDY 전용 차단 로직 |
| 네이버 검색 403/파싱 실패 | PC 버전 복잡한 DOM, 차단 | 모바일 버전(m.search.naver.com) + iPhone UA + `ZZCBS7C_fwcZFi3Z` 파싱 |
| "Shares Down 1.7%" 중립 분류 | 'down' 키워드 미포함 | '하락','내림','다운','감소','약세','내려','떨어' 추가 |

## 실행 환경
- **작업 디렉토리**: `C:\Users\kho\주식분석` (한글 경로)
- **Python**: `C:\Users\kho\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe` (lxml, bs4 설치됨)
- **데이터 캐시**: `C:\Users\kho\주식분석\data\` (HTML/XML 파일 저장)
- **출력**: `C:\Users\kho\주식분석\뉴스\YYYYMMDD_내종목뉴스.md`

## 크론 자동화 시 주의사항
1. **네이버 요청 간격**: 종목당 0.5초 `time.sleep()` 필수 (차단 방지)
2. **Google RSS 요청 간격**: 종목당 1초 권장
3. **파일 경로**: Windows 네이티브 경로(`C:\Users\...`) 또는 MSYS(`/c/Users/...`) 통일
4. **Telegram**: `--telegram` 플래그로 포맷 출력, 실제 전송은 게이트웨이 필요

## 테스트 명령
```bash
# 전체 파이프라인 실행 (Telegram 포맷 출력)
C:\Users\kho\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe \
  C:\c\Users\kho\주식분석\scripts\filter_my_stocks_news.py \
  --data-dir "C:\c\Users\kho\주식분석\data" \
  --output-dir "C:\c\Users\kho\주식분석" \
  --telegram

# 개별 파서 테스트
python -c "
from filter_my_stocks_news import parse_naver_search_news
items = parse_naver_search_news('data/naver_search_005930.html', '005930')
for i in items[:3]: print(i['title'], i['impact'], i['tickers'])
"
```

## 향후 개선 사항
1. **DART API 키 설정** → 실시간 공시 수집 활성화
2. **Daum 금융 대체 소스** 탐색 (네이버 금융 API, 키움증권 API 등)
3. **LLM 요약 연동** (Hermes chat 또는 OpenAI API) → 키워드 휴리스틱 대체
4. **Obsidian Vault 경로** 설정 자동화
5. **Telegram Bot Token** 설정 → 실제 알림 전송
6. **중복 제거 개선**: 제목 유사도(Levenshtein) 기반 클러스터링
7. **실시간성**: 웹훅/푸시 기반 수신으로 폴링 대체 검토