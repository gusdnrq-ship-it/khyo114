#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ============================================================
# 92종목 뉴스/공시 원본 데이터 수집 스크립트 (curl 기반)
# 매일 07:00 KST 실행 전 사전 수집용
# ============================================================

set -e

DATA_DIR="${1:-C:/Users/kho/주식분석/data}"
mkdir -p "$DATA_DIR"

USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS=(-H "User-Agent: $USER_AGENT" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" -H "Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")

echo "=== 92종목 원본 데이터 수집 시작: $(date) ==="
echo "데이터 디렉토리: $DATA_DIR"

# ------------------------------------------------------------------
# 국내 종목 (49개): 네이버 금융 뉴스 + 메인 + 와이즈리포트
# ------------------------------------------------------------------
DOMESTIC_TICKERS=(
    005930 000660 011790 046970 252670 453830 225460 373220
    006400 035420 035720 005380 051910 005490 068270 096770
    207940 012330 017670 033780 009830 010130 024110 032830
    034220 047810 058470 066570 091990 105560 138930 145020
    161390 192820 214150 214450 247540 251270 267250 285130
    293490 302440 316140 326030 340210 352820 357780 365340
)

echo ""
echo "[1/4] 국내 종목 네이버 금융 수집 (${#DOMESTIC_TICKERS[@]}개 종목)..."

for code in "${DOMESTIC_TICKERS[@]}"; do
    echo "  수집 중: $code"
    
    # 네이버 금융 메인 (시세, 기본정보)
    curl -s -L --max-time 30 "${HEADERS[@]}" \
        "https://finance.naver.com/item/main.naver?code=$code" \
        > "$DATA_DIR/naver_main_${code}.html"
    
    # 네이버 금융 뉴스 (1~2페이지) - news_news.naver 사용 (실제 뉴스 리스트)
    for page in 1 2; do
        curl -s -L --max-time 30 "${HEADERS[@]}" \
            "https://finance.naver.com/item/news_news.naver?code=$code&page=$page&sm=title_entity_id.basic" \
            > "$DATA_DIR/naver_news_${code}_p${page}.html"
    done
    
    # 와이즈리포트 기업개요
    curl -s -L --max-time 30 "${HEADERS[@]}" \
        "https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=$code" \
        > "$DATA_DIR/wisereport_company_${code}.html"
    
    # 와이즈리포트 밸류에이션/투자지표 (핵심)
    curl -s -L --max-time 30 "${HEADERS[@]}" \
        "https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx?cmp_cd=$code" \
        > "$DATA_DIR/wisereport_valuation_${code}.html"
    
    # 와이즈리포트 재무분석
    curl -s -L --max-time 30 "${HEADERS[@]}" \
        "https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx?cmp_cd=$code" \
        > "$DATA_DIR/wisereport_financial_${code}.html"
    
    # 와이즈리포트 컨센서스
    curl -s -L --max-time 30 "${HEADERS[@]}" \
        "https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd=$code" \
        > "$DATA_DIR/wisereport_consensus_${code}.html"
    
    sleep 1.5  # IP 차단 방지
done

# ------------------------------------------------------------------
# 해외 종목 (43개): Google News RSS
# ------------------------------------------------------------------
OVERSEAS_TICKERS=(
    NVDA NVDY QQQ TQQQ AAPL MSFT GOOGL AMZN META TSLA
    AVGO AMD INTC CRM ORCL ADBE NFLX CSCO PEP COST
    TMUS V MA JPM BAC WMT HD PG JNJ UNH MRK ABBV
    PFE TMO DHR ABT LLY BMY AMGN GILD ISRG
)

echo ""
echo "[2/4] 해외 종목 Google News RSS 수집 (${#OVERSEAS_TICKERS[@]}개 종목)..."

for symbol in "${OVERSEAS_TICKERS[@]}"; do
    echo "  수집 중: $symbol"
    
    curl -s -L --max-time 30 "${HEADERS[@]}" \
        "https://news.google.com/rss/search?q=${symbol}+stock&hl=en&gl=US&ceid=US:en" \
        > "$DATA_DIR/google_news_${symbol}.xml"
    
    sleep 1
done

# ------------------------------------------------------------------
# DART 공시 수집 (OpenDART API 필요 - API 키 필수)
# ------------------------------------------------------------------
echo ""
echo "[3/4] DART 공시 수집..."

DART_API_KEY="${DART_API_KEY:-}"
if [ -n "$DART_API_KEY" ]; then
    # 최근 1일 공시 수집 (page_count=100)
    curl -s -L --max-time 60 \
        "https://opendart.fss.or.kr/api/list.xml?crtfc_key=${DART_API_KEY}&page_count=100" \
        > "$DATA_DIR/dart_list.xml"
    echo "  DART 공시 수집 완료"
else
    echo "  ⚠️  DART_API_KEY 환경변수 미설정 - 건너뜀"
    # 빈 파일 생성 (파싱 스크립트가 에러 안 나도록)
    echo '<?xml version="1.0"?><result><list></list></result>' > "$DATA_DIR/dart_list.xml"
fi

# ------------------------------------------------------------------
# 다음 금융 뉴스 수집 (API)
# ------------------------------------------------------------------
echo ""
echo "[4/4] 다음 금융 뉴스 수집..."

curl -s -L --max-time 30 "${HEADERS[@]}" \
    "https://finance.daum.net/api/news/list?category=stock&limit=100" \
    > "$DATA_DIR/daum_news.json"

echo ""
echo "=== 원본 데이터 수집 완료: $(date) ==="
echo "저장 위치: $DATA_DIR"
ls -la "$DATA_DIR" | head -30