---
date: {{DATE}}
title: {{NAME}} ({{CODE}}) 종합 투자 분석 리포트
code: "{{CODE}}"
name: {{NAME}}
sector: {{SECTOR}}
market: {{MARKET}}
tags: [주식분석, {{CODE}}, {{SECTOR}}, {{MARKET}}, 투자리포트]
source: stock-analysis skill
---

# {{NAME}} ({{CODE}}) 종합 투자 분석 리포트

**생성일시:** {{DATETIME}} KST
**데이터 기준일:** {{DATE}}

---

## 📊 기본 시세 정보

| 지표 | 값 |
|------|-----|
| 현재가 | {{CURRENT_PRICE}}원 |
| 전일대비 | {{CHANGE}}원 ({{CHANGE_PCT}}%) |
| 시가 | {{OPEN_PRICE}}원 |
| 고가 | {{HIGH_PRICE}}원 |
| 저가 | {{LOW_PRICE}}원 |
| 거래량 | {{VOLUME}}주 |
| 거래대금 | {{TRADING_VALUE}}억원 |

---

## 📈 핵심 투자지표

| 지표 | 값 | 업종평균 | 비고 |
|------|-----|----------|------|
| PER | {{PER}}x | {{INDUSTRY_PER}}x | {{PER_NOTE}} |
| PBR | {{PBR}}x | {{INDUSTRY_PBR}}x | {{PBR_NOTE}} |
| EPS | {{EPS}}원 | - | |
| BPS | {{BPS}}원 | - | |
| 현금배당수익률 | {{DIVIDEND_YIELD}}% | {{INDUSTRY_DIVIDEND}}% | {{DIVIDEND_NOTE}} |
| 시가배당률 | {{DIVIDEND_YIELD}}% | - | |
| 시가총액 | {{MARKET_CAP}}조원 | - | {{MARKET_CAP_RANK}} |

---

## 🏢 기업 개요

| 항목 | 내용 |
|------|------|
| 대표이사 | {{CEO}} |
| 본사 | {{HEADQUARTERS}} |
| 설립일 | {{FOUNDED_DATE}} |
| 상장일 | {{LISTED_DATE}} |
| 종업원수 | {{EMPLOYEES}}명 |
| 홈페이지 | {{WEBSITE}} |

---

## 💰 재무 하이라이트 (단위: 억원)

| 항목 | {{YEAR}} | {{PREV_YEAR}} | {{PREV2_YEAR}} | YoY |
|------|------|------|------|-----|
| 매출액 | {{REVENUE}} | {{PREV_REVENUE}} | {{PREV2_REVENUE}} | {{REVENUE_YOY}} |
| 영업이익 | {{OP_PROFIT}} | {{PREV_OP_PROFIT}} | {{PREV2_OP_PROFIT}} | {{OP_PROFIT_YOY}} |
| 당기순이익 | {{NET_PROFIT}} | {{PREV_NET_PROFIT}} | {{PREV2_NET_PROFIT}} | {{NET_PROFIT_YOY}} |
| 자산총계 | {{TOTAL_ASSETS}} | {{PREV_TOTAL_ASSETS}} | {{PREV2_TOTAL_ASSETS}} | - |
| 자본총계 | {{TOTAL_EQUITY}} | {{PREV_TOTAL_EQUITY}} | {{PREV2_TOTAL_EQUITY}} | - |
| 부채총계 | {{TOTAL_LIABILITIES}} | {{PREV_TOTAL_LIABILITIES}} | {{PREV2_TOTAL_LIABILITIES}} | - |

---

## 📊 재무분석 지표

| 지표 | 값 | 업종평가 | 비고 |
|------|-----|----------|------|
| ROE | {{ROE}}% | {{INDUSTRY_ROE}}% | {{ROE_NOTE}} |
| ROA | {{ROA}}% | {{INDUSTRY_ROA}}% | {{ROA_NOTE}} |
| 영업이익률 | {{OP_MARGIN}}% | {{INDUSTRY_OP_MARGIN}}% | {{OP_MARGIN_NOTE}} |
| 순이익률 | {{NET_MARGIN}}% | {{INDUSTRY_NET_MARGIN}}% | {{NET_MARGIN_NOTE}} |
| 부채비율 | {{DEBT_RATIO}}% | {{INDUSTRY_DEBT_RATIO}}% | {{DEBT_RATIO_NOTE}} |
| 유동비율 | {{CURRENT_RATIO}}% | {{INDUSTRY_CURRENT_RATIO}}% | {{CURRENT_RATIO_NOTE}} |
| 매출액증가율 | {{REVENUE_GROWTH}}% | {{INDUSTRY_REVENUE_GROWTH}}% | {{REVENUE_GROWTH_NOTE}} |
| 영업이익증가율 | {{OP_PROFIT_GROWTH}}% | {{INDUSTRY_OP_PROFIT_GROWTH}}% | {{OP_PROFIT_GROWTH_NOTE}} |

---

## 📰 최신 뉴스 (Top 5)

| 날짜 | 제목 | 출처 | 요약 |
|------|------|------|------|
| {{NEWS_DATE_1}} | {{NEWS_TITLE_1}} | {{NEWS_SOURCE_1}} | {{NEWS_SUMMARY_1}} |
| {{NEWS_DATE_2}} | {{NEWS_TITLE_2}} | {{NEWS_SOURCE_2}} | {{NEWS_SUMMARY_2}} |
| {{NEWS_DATE_3}} | {{NEWS_TITLE_3}} | {{NEWS_SOURCE_3}} | {{NEWS_SUMMARY_3}} |
| {{NEWS_DATE_4}} | {{NEWS_TITLE_4}} | {{NEWS_SOURCE_4}} | {{NEWS_SUMMARY_4}} |
| {{NEWS_DATE_5}} | {{NEWS_TITLE_5}} | {{NEWS_SOURCE_5}} | {{NEWS_SUMMARY_5}} |

---

## 🎯 주요 투자 포인트

### 강점 (Bull Case)
{{BULL_POINTS}}

### 약점 (Bear Case)
{{BEAR_POINTS}}

---

## 🏷️ 태그

`#주식분석 #{{CODE}} #{{SECTOR}} #{{MARKET}} #투자리포트`

---

*본 리포트 Hermes Agent stock-analysis 스킬로 자동 생성되었습니다.*
*데이터 출처: 네이버 금융, 와이즈리포트/FnGuide, Google News RSS*
*투자 판단은 본인의 책임 하에 신중히 결정하시기 바랍니다.*