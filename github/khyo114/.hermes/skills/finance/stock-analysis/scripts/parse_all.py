#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 종목 파싱 스크립트 - 네이버 금융, 와이즈리포트, Google News RSS 파싱
stock-analysis 스킬의 재사용 가능한 파싱 모듈

사용법:
    python parse_all.py --data-dir "C:\path\to\data" --output "C:\path\to\parsed_all.json"
"""
import os
import re
import json
import argparse
from bs4 import BeautifulSoup

def read_html_with_fallback(filepath):
    """UTF-8 실패 시 CP949로 재시도"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='cp949') as f:
            return f.read()

def parse_naver_main(html, code):
    """네이버 금융 메인 페이지 파싱 - 시세 정보"""
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    
    # 첫 번째 blind dl - 현재가, 전일대비, 시가/고가/저가, 거래량/거래대금
    blind_dls = soup.find_all('dl', class_='blind')
    if len(blind_dls) >= 1:
        first_dl = blind_dls[0]
        for dd in first_dl.find_all('dd'):
            text = dd.get_text(strip=True)
            if '현재가' in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '현재가' and i+1 < len(parts):
                        result['현재가'] = parts[i+1].replace(',', '')
            elif '전일대비' in text:
                match = re.search(r'전일대비\s+(상승|하락|보합)\s+([\d,]+)\s+(플러스|마이너스)\s+([\d.]+)\s*퍼센트', text)
                if match:
                    result['전일대비_방향'] = match.group(1)
                    result['전일대비_금액'] = match.group(2).replace(',', '')
                    result['전일대비_부호'] = match.group(3)
                    result['전일대비_률'] = match.group(4)
            elif '전일가' in text and '전일대비' not in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '전일가' and i+1 < len(parts):
                        result['전일가'] = parts[i+1].replace(',', '')
            elif '시가' in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '시가' and i+1 < len(parts):
                        result['시가'] = parts[i+1].replace(',', '')
            elif '고가' in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '고가' and i+1 < len(parts):
                        result['고가'] = parts[i+1].replace(',', '')
            elif '저가' in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '저가' and i+1 < len(parts):
                        result['저가'] = parts[i+1].replace(',', '')
            elif '거래량' in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '거래량' and i+1 < len(parts):
                        result['거래량'] = parts[i+1].replace(',', '')
            elif '거래대금' in text:
                parts = text.split()
                for i, p in enumerate(parts):
                    if p == '거래대금' and i+1 < len(parts):
                        result['거래대금'] = parts[i+1].replace(',', '')
    
    # 두 번째 blind dl (rate_info 내부) - 등락률 상세
    if len(blind_dls) >= 2:
        second_dl = blind_dls[1]
        for dd in second_dl.find_all('dd'):
            text = dd.get_text(strip=True)
            if '등락률' in text:
                match = re.search(r'등락률\s+([+-]?[\d.]+)\s*%', text)
                if match:
                    result['등락률'] = match.group(1)
    
    # 시세 테이블 - PER, PBR, 시가배당률, 52주 최고/최저, 시가총액, 외국인비율
    tables = soup.find_all('table')
    for table in tables:
        ths = table.find_all('th')
        for th in ths:
            th_text = th.get_text(strip=True)
            td = th.find_next_sibling('td')
            if not td:
                continue
            td_text = td.get_text(strip=True)
            
            blind_span = td.find('span', class_='blind')
            if blind_span:
                td_text = blind_span.get_text(strip=True)
            
            em_tag = td.find('em')
            if em_tag:
                td_text = em_tag.get_text(strip=True)
            
            if 'PER' in th_text and '업종' not in th_text:
                result['PER'] = td_text.replace(',', '')
            elif 'PBR' in th_text:
                result['PBR'] = td_text.replace(',', '')
            elif '시가배당률' in th_text:
                result['시가배당률'] = td_text.replace(',', '')
            elif '52주' in th_text and ('최고' in th_text or '최저' in th_text):
                if '최고' in th_text:
                    result['52주_최고'] = td_text.replace(',', '')
                if '최저' in th_text:
                    result['52주_최저'] = td_text.replace(',', '')
            elif '시가총액' in th_text:
                result['시가총액'] = td_text.replace(',', '')
            elif '외국인' in th_text and ('비율' in th_text or '소진율' in th_text):
                result['외국인비율'] = td_text.replace(',', '')
    
    return result


def parse_naver_news(html, code):
    """네이버 금융 뉴스 파싱"""
    soup = BeautifulSoup(html, 'html.parser')
    news_list = []
    
    table = soup.find('table', class_='type5')
    if table:
        rows = table.find_all('tr')
        for row in rows:
            title_td = row.find('td', class_='title')
            info_td = row.find('td', class_='info')
            if title_td:
                a_tag = title_td.find('a')
                if a_tag:
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get('href', '')
                    date = info_td.get_text(strip=True) if info_td else ''
                    news_list.append({
                        'title': title,
                        'link': link,
                        'date': date
                    })
    
    return news_list[:10]


def parse_wisereport_company(html, code):
    """와이즈리포트 기업개요 파싱"""
    if len(html) < 500:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    
    tables = soup.find_all('table')
    for table in tables:
        if 'gHead' in table.get('class', []):
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    th_text = th.get_text(strip=True)
                    td_text = td.get_text(strip=True)
                    if '대표이사' in th_text:
                        result['대표이사'] = td_text
                    elif '본사' in th_text:
                        result['본사'] = td_text
                    elif '홈페이지' in th_text:
                        result['홈페이지'] = td_text
                    elif '설립일' in th_text:
                        result['설립일'] = td_text
                    elif '상장일' in th_text:
                        result['상장일'] = td_text
                    elif '종업원' in th_text:
                        result['종업원수'] = td_text
    
    for table in tables:
        ths = table.find_all('th')
        for th in ths:
            th_text = th.get_text(strip=True)
            td = th.find_next_sibling('td')
            if not td:
                continue
            td_text = td.get_text(strip=True)
            if '매출액' in th_text:
                result['매출액'] = td_text.replace(',', '')
            elif '영업이익' in th_text:
                result['영업이익'] = td_text.replace(',', '')
            elif '당기순이익' in th_text:
                result['당기순이익'] = td_text.replace(',', '')
            elif '자산총계' in th_text:
                result['자산총계'] = td_text.replace(',', '')
            elif '자본총계' in th_text:
                result['자본총계'] = td_text.replace(',', '')
            elif '부채총계' in th_text:
                result['부채총계'] = td_text.replace(',', '')
    
    return result


def parse_wisereport_valuation(html, code):
    """와이즈리포트 밸류에이션/투자지표 파싱"""
    if len(html) < 500:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    
    tables = soup.find_all('table', class_='cmp-table')
    for table in tables:
        dts = table.find_all('dt')
        for dt in dts:
            dt_text = dt.get_text(strip=True)
            b_tag = dt.find('b', class_='num')
            if b_tag:
                val = b_tag.get_text(strip=True).replace(',', '')
                if 'EPS' in dt_text and '예상' not in dt_text:
                    result['EPS'] = val
                elif 'BPS' in dt_text:
                    result['BPS'] = val
                elif 'PER' in dt_text and '업종' not in dt_text:
                    result['PER'] = val
                elif '업종PER' in dt_text:
                    result['업종PER'] = val
                elif 'PBR' in dt_text:
                    result['PBR'] = val
                elif '현금배당수익률' in dt_text or '배당수익률' in dt_text:
                    result['현금배당수익률'] = val
                elif 'EV/EBITDA' in dt_text:
                    result['EV_EBITDA'] = val
    
    return result


def parse_wisereport_financial(html, code):
    """와이즈리포트 재무분석 파싱"""
    if len(html) < 500:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    
    tables = soup.find_all('table')
    for table in tables:
        ths = table.find_all('th')
        for th in ths:
            th_text = th.get_text(strip=True)
            td = th.find_next_sibling('td')
            if not td:
                continue
            td_text = td.get_text(strip=True).replace(',', '')
            
            if 'ROE' in th_text:
                result['ROE'] = td_text
            elif 'ROA' in th_text:
                result['ROA'] = td_text
            elif '영업이익률' in th_text:
                result['영업이익률'] = td_text
            elif '순이익률' in th_text:
                result['순이익률'] = td_text
            elif '부채비율' in th_text:
                result['부채비율'] = td_text
            elif '유동비율' in th_text:
                result['유동비율'] = td_text
            elif '매출액증가율' in th_text:
                result['매출액증가율'] = td_text
            elif '영업이익증가율' in th_text:
                result['영업이익증가율'] = td_text
    
    return result


def parse_google_news_rss(xml, symbol):
    """Google News RSS 파싱"""
    soup = BeautifulSoup(xml, 'xml')
    news_list = []
    
    items = soup.find_all('item')
    for item in items[:15]:
        title_tag = item.find('title')
        link_tag = item.find('link')
        pub_date_tag = item.find('pubDate')
        desc_tag = item.find('description')
        
        title = title_tag.get_text(strip=True) if title_tag else ''
        link = link_tag.get_text(strip=True) if link_tag else ''
        pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else ''
        desc = desc_tag.get_text(strip=True) if desc_tag else ''
        
        title = title.replace('<![CDATA[', '').replace(']]>', '')
        desc = desc.replace('<![CDATA[', '').replace(']]>', '')
        
        news_list.append({
            'title': title,
            'link': link,
            'date': pub_date,
            'summary': desc[:200] if desc else ''
        })
    
    return news_list


def parse_stock(data_dir, code, info):
    """단일 종목 파싱"""
    print(f"Parsing {info['name']} ({code})...")
    
    stock_data = {
        'code': code,
        'name': info['name'],
        'sector': info['sector'],
        'market': info['market'],
        'basic': {},
        'company': {},
        'valuation': {},
        'financial': {},
        'news': []
    }
    
    if info['market'] == '국내':
        # 네이버 메인
        main_path = os.path.join(data_dir, f"naver_main_{code}.html")
        if os.path.exists(main_path):
            html = read_html_with_fallback(main_path)
            stock_data['basic'] = parse_naver_main(html, code)
        
        # 네이버 뉴스
        news_path = os.path.join(data_dir, f"naver_news_{code}_p1.html")
        if os.path.exists(news_path):
            html = read_html_with_fallback(news_path)
            stock_data['news'] = parse_naver_news(html, code)
        
        # 와이즈리포트 기업개요
        company_path = os.path.join(data_dir, f"wisereport_company_{code}.html")
        if os.path.exists(company_path):
            html = read_html_with_fallback(company_path)
            stock_data['company'] = parse_wisereport_company(html, code)
        
        # 와이즈리포트 밸류에이션
        valuation_path = os.path.join(data_dir, f"wisereport_valuation_{code}.html")
        if os.path.exists(valuation_path):
            html = read_html_with_fallback(valuation_path)
            stock_data['valuation'] = parse_wisereport_valuation(html, code)
        
        # 와이즈리포트 재무분석
        financial_path = os.path.join(data_dir, f"wisereport_financial_{code}.html")
        if os.path.exists(financial_path):
            html = read_html_with_fallback(financial_path)
            stock_data['financial'] = parse_wisereport_financial(html, code)
    else:
        # Google News RSS
        rss_path = os.path.join(data_dir, f"google_news_{code}.xml")
        if os.path.exists(rss_path):
            with open(rss_path, 'r', encoding='utf-8') as f:
                xml = f.read()
            stock_data['news'] = parse_google_news_rss(xml, code)
    
    return stock_data


def main():
    parser = argparse.ArgumentParser(description='주식 데이터 파싱')
    parser.add_argument('--data-dir', required=True, help='데이터 파일 디렉토리')
    parser.add_argument('--output', required=True, help='출력 JSON 파일 경로')
    args = parser.parse_args()
    
    # 종목 매핑 (필요시 외부 설정 파일로 분리 가능)
    stocks = {
        "005930": {"name": "삼성전자", "sector": "반도체_전자", "market": "국내"},
        "252670": {"name": "KODEX 200", "sector": "ETF_지수", "market": "국내"},
        "453830": {"name": "TIGER K방산우주", "sector": "ETF_방산우주", "market": "국내"},
        "225460": {"name": "토박스코리아", "sector": "유통_소비재", "market": "국내"},
        "011790": {"name": "SKC", "sector": "화학_소재", "market": "국내"},
        "047040": {"name": "대우건설", "sector": "건설", "market": "국내"},
        "NVDY": {"name": "NVDY", "sector": "ETF_커버드콜", "market": "해외"},
        "NVDA": {"name": "엔비디아", "sector": "반도체_AI", "market": "해외"},
        "QQQ": {"name": "QQQ", "sector": "ETF_나스닥100", "market": "해외"},
        "SPY": {"name": "SPY", "sector": "ETF_SP500", "market": "해외"},
    }
    
    result = {}
    for code, info in stocks.items():
        result[code] = parse_stock(args.data_dir, code, info)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nParsed data saved to {args.output}")


if __name__ == '__main__':
    main()