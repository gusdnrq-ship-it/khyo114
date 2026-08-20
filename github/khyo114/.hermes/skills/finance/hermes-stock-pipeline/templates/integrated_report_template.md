---
date: {{DATE}}
title: {{DATE}} 종합 투자 분석 리포트 ({{COUNT}}종목)
tags: [주식분석, 종합리포트, {{DATE}}, 투자리포트]
source: stock-analysis skill
---

# {{DATE}} 종합 투자 분석 리포트 ({{COUNT}}종목)

**생성일시:** {{DATETIME}} KST

---

## 📋 종목 요약

| 구분 | 종목코드 | 종목명 | 현재가 | 전일대비 | PER | PBR | 섹터 | 시장 |
|------|---------|--------|--------|----------|-----|-----|------|------|
{{STOCK_SUMMARY_TABLE}}

---

## 📈 섹터별 요약

### 반도체/전자
{{SECTOR_SEMICONDUCTOR}}

### ETF
{{SECTOR_ETF}}

### 기타
{{SECTOR_OTHER}}

---

## 🎯 포트폴리오 액션 제안

| 액션 | 종목 | 사유 |
|------|------|------|
{{ACTION_TABLE}}

---

## 📊 상세 리포트

{{INDIVIDUAL_REPORTS}}

---

*본 리포트는 Hermes Agent stock-analysis 스킬로 자동 생성되었습니다.*
*데이터 출처: 네이버 금융, 와이즈리포트/FnGuide, Google News RSS*
*투자 판단은 본인의 책임 하에 신중히 결정하시기 바랍니다.*