# ��시디언 저장 및 리포트 생성 패턴 (이 세션 검증��)

## 개요
수집된 데이터를 바탕으로 종합 투자 분석 리포트를 생성하고, ��시디언 볼트 규칙에 따라 구조화하여 저장하는 패턴.

## ��시디언 저장 규칙

### 디렉토리 구조
```
주식분석/
├── {YYYYMMDD}_종합투자분석리포트.md          # 전체 종목 통합 리포트
├── {회사명}/
│   └── {YYYYMMDD}_{회사명}.md              # 개별 종목 상세 리포트
```

### 파일 명명 규칙
- **통합 리포트**: `{YYYYMMDD}_종합투자분석리포트.md`
- **개별 리포트**: `주식분석/{회사명}/{YYYYMMDD}_{회사명}.md`

### 필수 태그 (YAML 프론트매터 또는 본문 상단)
```
태그: #주식분석 #{종목코드} #{��터_슬러그} #{시장구분} #투자리포트
```
예: `#주식분석 #005930 #반도체_전자 #국내 #투자리포트`

## 리포트 구성 ��플릿

### 1. 통합 리포트 (종합투자분석리포트.md)
```markdown
# 종합 투자 분석 리포트
**생성일시**: {YYYY년 MM월 DD일 HH:MM}
**대상 종목**: N개 (국내 X개, 해외 Y개)
**데이터 소스**: 네이버 금��, 와이즈리포트(FnGuide), Google News RSS

## {종목명} ({종목코드})
**��터**: {��터} | **시장**: {국내/해외}

### ��� 기본 시세 정보
- **현재가**: {��}
- **시가총액**: {��}
- ...

### ��� 핵심 투자지표 (와이즈리포트)
- **PER**: {��}
- **PBR**: {��}
- ...

### ��� 재무 하이라이트
- **매출액**: {��}
- **영업이익**: {��}
- ...

### ��� 최신 뉴스 헤드라인
1. {뉴스 제목}
2. ...

---
## ��� 종합 투자 포인트 요약

### {��터명}
- **{종목명}**: 현재가 {��}, PER {��}, PBR {��}, 배당수익률 {��}

---
## ������ 유의사항
- 본 리포트는 공개된 데이터를 바탕으로 자동 생성되었습니다.
- 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
- 실시간 시세와 다를 수 있으니 투자 전 최신 정보 확인 바랍니다.
- 데이터 기준일: {YYYYMMDD}
```

### 2. 개별 리포트 ({회사명}/{YYYYMMDD}_{회사명}.md)
```markdown
# {종목명} ({종목코드}) 투자 분석 리포트
**생성일시**: {YYYY년 MM월 DD일 HH:MM}
**��터**: {��터} | **시장**: {국내/해외}

태그: #주식분석 #{종목코드} #{��터_슬러그} #{시장구분} #투자리포트

## ��� 기본 시세 정보
...

## ��� 핵심 투자지표
...

## ��� 재무 하이라이트
...

## ��� 최신 뉴스
...
```

## 구현 패턴 (Python)

```python
import os
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")
# Windows 네이티브 경로 사용 필수 (MSYS /c/... 경로는 Python에서 작동 안 함)
obsidian_dir = r"C:\Users\kho\주식분석"  # 원시 문자열(r'...') 또는 \\ 이스케이프 사용

# 1. 통합 리포트 저장
report_path = os.path.join(obsidian_dir, f"{today}_종합투자분석리포트.md")
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_content)

# 2. 개별 리포트 저장
for name, data in all_data.items():
    stock_dir = os.path.join(obsidian_dir, name)
    os.makedirs(stock_dir, exist_ok=True)
    
    individual_path = os.path.join(stock_dir, f"{today}_{name}.md")
    with open(individual_path, 'w', encoding='utf-8') as f:
        f.write(individual_content)
```

## 재사용 가능한 템플릿 파일 (이 세션에서 생성)
- `templates/integrated_report_template.md` — 통합 리포트 마크다운 템플릿
- `templates/individual_report_template.md` — 개별 종목 리포트 마크다운 템플릿
- `scripts/parse_all.py` — 전체 종목 파싱 스크립트 (네이버+와이즈리포트+Google RSS)
- `scripts/generate_reports.py` — 파싱된 JSON으로부터 리포트 생성 스크립트

## ⚠️ Windows 경로 주의사항
- **MSYS/Git Bash 경로(`/c/Users/...`)는 Python `open()`에서 작동하지 않음** → `FileNotFoundError` 발생
- 반드시 **Windows 네이티브 경로(`C:\Users\...`)** 사용
- Python 문자열에서 백슬래시 이스케이프: `r"C:\Users\kho\주식분석"` (raw string) 또는 `"C:\\Users\\kho\\주식분석"`
- `terminal` 호출 시 `workdir`도 네이티브 경로로 지정: `workdir="C:\\Users\\kho\\주식분석"`

## 크론 자동화 패턴 (매일 정기 리포트) — 2026-08-16 요청사항
```bash
# 관심 종목 N개 매일 오전 8시 실행
hermes cron create \
  --schedule "0 8 * * *" \
  --prompt "관심 종목 [005930,252670,453830,225460,011790,047040,NVDY,NVDA,QQQ,SPY] 일일 종합 투자 분석 리포트 생성 및 옵시디언 저장" \
  --skills stock-analysis \
  --name "주식 일일 리포트"
```

## 이 세션 결과 (2026-08-16)
- **통합 리포트**: `20260816_종합투자분석리포트.md` (10개 종목)
- **개별 리포트**: 10개 생성 (각 종목별 디렉토리 하위)
- **태그 적용**: 전 종목 `#주식분석 #{종목코드} #{섹터} #{시장} #투자리포트`
- **파싱 스크립트**: `parse_all.py`, `generate_reports.py` 저장 및 검증 완료