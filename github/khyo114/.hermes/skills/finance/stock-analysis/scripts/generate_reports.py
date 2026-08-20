#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리포트 생성 스크립트 - 파싱된 JSON으로부터 옵시디언 형식 마크다운 리포트 생성
stock-analysis 스킬의 재사용 가능한 리포트 생성 모듈

사용법:
    python generate_reports.py --parsed "C:\path\to\parsed_all.json" --obsidian-dir "C:\path\to\obsidian"
"""
import os
import json
import argparse
from datetime import datetime

# 섹터 슬러그 매핑
SECTOR_SLUG_MAP = {
    "반도체_전자": "반도체_전자",
    "ETF_지수": "ETF_지수",
    "ETF_방산우주": "ETF_방산우주",
    "유통_소비재": "유통_소비재",
    "화학_소재": "화학_소재",
    "건설": "건설",
    "ETF_커버드콜": "ETF_커버드콜",
    "반도체_AI": "반도체_AI",
    "ETF_나스닥100": "ETF_나스닥100",
    "ETF_SP500": "ETF_SP500",
}

MARKET_SLUG = {"국내": "국내", "해외": "해외"}


def format_dict_section(data, prefix=""):
    """딕셔너리를 마크다운 리스트로 변환"""
    lines = []
    for key, val in data.items():
        if val:
            lines.append(f"- **{key}**: {val}")
    return "\n".join(lines)


def format_news_section(news_list, max_items=10):
    """뉴스 리스트를 마크다운으로 변환"""
    if not news_list:
        return ""
    
    lines = []
    for i, news in enumerate(news_list[:max_items], 1):
        title = news.get('title', '')
        date = news.get('date', '')
        link = news.get('link', '')
        summary = news.get('summary', '')
        if title:
            lines.append(f"### {i}. {title}")
            lines.append(f"**날짜**: {date}")
            if link:
                lines.append(f"**링크**: {link}")
            if summary:
                lines.append(f"**요약**: {summary}")
            lines.append("")
    return "\n".join(lines)


def generate_integrated_report(all_data, today, today_display):
    """통합 리포트 생성"""
    domestic_count = sum(1 for v in all_data.values() if v['market'] == '국내')
    overseas_count = sum(1 for v in all_data.values() if v['market'] == '해외')
    
    lines = []
    lines.append("# 종합 투자 분석 리포트")
    lines.append(f"**생성일시**: {today_display}")
    lines.append(f"**대상 종목**: {len(all_data)}개 (국내 {domestic_count}개, 해외 {overseas_count}개)")
    lines.append("**데이터 소스**: 네이버 금융, 와이즈리포트(FnGuide), Google News RSS")
    lines.append("")
    
    # 종목별 섹션
    for code, data in all_data.items():
        name = data['name']
        sector = data['sector']
        market = data['market']
        
        lines.append(f"## {name} ({code})")
        lines.append(f"**섹터**: {sector} | **시장**: {market}")
        lines.append("")
        
        if data['basic']:
            lines.append("### 📈 기본 시세 정보")
            lines.append(format_dict_section(data['basic']))
            lines.append("")
        
        if data['valuation']:
            lines.append("### 📊 핵심 투자지표 (와이즈리포트)")
            lines.append(format_dict_section(data['valuation']))
            lines.append("")
        
        if data['company'] and any(k in data['company'] for k in ['매출액', '영업이익', '당기순이익', '자산총계', '자본총계', '부채총계', '대표이사', '본사', '설립일', '상장일', '종업원수']):
            lines.append("### 💰 재무 하이라이트")
            comp = data['company']
            for key in ['매출액', '영업이익', '당기순이익', '자산총계', '자본총계', '부채총계', '대표이사', '본사', '설립일', '상장일', '종업원수']:
                if key in comp and comp[key]:
                    lines.append(f"- **{key}**: {comp[key]}")
            lines.append("")
        
        if data['financial']:
            lines.append("### 📋 재무분석 지표")
            lines.append(format_dict_section(data['financial']))
            lines.append("")
        
        if data['news']:
            lines.append("### 📰 최신 뉴스 헤드라인")
            for i, news in enumerate(data['news'][:5], 1):
                title = news.get('title', '')
                date = news.get('date', '')
                if title:
                    lines.append(f"{i}. {title} ({date})")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # 종합 투자 포인트 요약
    lines.append("## 📌 종합 투자 포인트 요약")
    lines.append("")
    
    sectors = {}
    for code, data in all_data.items():
        sector = data['sector']
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(data)
    
    for sector, stocks in sectors.items():
        lines.append(f"### {sector}")
        for s in stocks:
            basic = s['basic']
            val = s['valuation']
            name = s['name']
            code = s['code']
            cur = basic.get('현재가', 'N/A')
            per = val.get('PER', basic.get('PER', 'N/A'))
            pbr = val.get('PBR', basic.get('PBR', 'N/A'))
            div = val.get('현금배당수익률', basic.get('시가배당률', 'N/A'))
            lines.append(f"- **{name} ({code})**: 현재가 {cur}, PER {per}, PBR {pbr}, 배당수익률 {div}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## ⚠️ 유의사항")
    lines.append("- 본 리포트는 공개된 데이터를 바탕으로 자동 생성되었습니다.")
    lines.append("- 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.")
    lines.append("- 실시간 시세와 다를 수 있으니 투자 전 최신 정보 확인 바랍니다.")
    lines.append(f"- 데이터 기준일: {today}")
    
    return "\n".join(lines)


def generate_individual_report(data, today, today_display):
    """개별 종목 리포트 생성"""
    name = data['name']
    code = data['code']
    sector = data['sector']
    market = data['market']
    
    sector_slug = SECTOR_SLUG_MAP.get(sector, sector)
    market_slug = MARKET_SLUG.get(market, market)
    
    lines = []
    lines.append(f"# {name} ({code}) 투자 분석 리포트")
    lines.append(f"**생성일시**: {today_display}")
    lines.append(f"**섹터**: {sector} | **시장**: {market}")
    lines.append("")
    lines.append(f"태그: #주식분석 #{code} #{sector_slug} #{market_slug} #투자리포트")
    lines.append("")
    
    if data['basic']:
        lines.append("## 📈 기본 시세 정보")
        lines.append(format_dict_section(data['basic']))
        lines.append("")
    
    if data['valuation']:
        lines.append("## 📊 핵심 투자지표 (와이즈리포트)")
        lines.append(format_dict_section(data['valuation']))
        lines.append("")
    
    if data['company']:
        lines.append("## 💰 재무 하이라이트")
        lines.append(format_dict_section(data['company']))
        lines.append("")
    
    if data['financial']:
        lines.append("## 📋 재무분석 지표")
        lines.append(format_dict_section(data['financial']))
        lines.append("")
    
    if data['news']:
        lines.append("## 📰 최신 뉴스")
        lines.append(format_news_section(data['news'], max_items=10))
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='리포트 생성')
    parser.add_argument('--parsed', required=True, help='파싱된 JSON 파일 경로')
    parser.add_argument('--obsidian-dir', required=True, help='옵시디언 저장 디렉토리')
    args = parser.parse_args()
    
    with open(args.parsed, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    today = datetime.now().strftime("%Y%m%d")
    today_display = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    # 1. 통합 리포트 생성 및 저장
    integrated_report = generate_integrated_report(all_data, today, today_display)
    integrated_path = os.path.join(args.obsidian_dir, f"{today}_종합투자분석리포트.md")
    with open(integrated_path, 'w', encoding='utf-8') as f:
        f.write(integrated_report)
    print(f"통합 리포트 저장: {integrated_path}")
    
    # 2. 개별 리포트 생성 및 저장
    for code, data in all_data.items():
        name = data['name']
        stock_dir = os.path.join(args.obsidian_dir, name)
        os.makedirs(stock_dir, exist_ok=True)
        
        individual_report = generate_individual_report(data, today, today_display)
        individual_path = os.path.join(stock_dir, f"{today}_{name}.md")
        with open(individual_path, 'w', encoding='utf-8') as f:
            f.write(individual_report)
        print(f"개별 리포트 저장: {individual_path}")
    
    print("\n✅ 모든 리포트 생성 완료!")


if __name__ == '__main__':
    main()