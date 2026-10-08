# Windows 브라우저 타임아웃/인코딩 이슈 재현 레시피 및 수정 패턴

## 재현 시나리오
- Windows Git Bash 환경에서 `browser_navigate` 5~7회 이상 호출 시 300초 타임아웃
- 백그라운드 리더 스레드에서 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbf` 발생
- 실제로는 프로세스가 정상 완료(exit_code=0)되었으나 출력 스레드에서 디코딩 실패로 로그만 오염

## 검증된 우회 패턴 (이 세션에서 확인)

### 1. 백그라운드 실행 + 알림 (가장 효과적)
```bash
# 터미널에서 직접 실행
hermes chat -q "프롬프트" -s stock-analysis &
# 또는 프로그래밍적으로
terminal(command="hermes chat -q '...' -s stock-analysis", background=true, notify_on_complete=true, timeout=600)
```

### 2. 브라우저 완전 배제 (권장)
- `web_search` + `web_extract` 조합만으로 1차 수집
- 금융 사이트: 네이버금융, 와이즈리포트(FnGuide), 네이버뉴스는 curl/터미널로 직접 접근 가능
- `curl -s "https://finance.naver.com/item/news.naver?code=005930&page=1" -H "User-Agent: Mozilla/5.0"`

### 3. 인코딩 강제 설정
```bash
# Windows 콘솔 UTF-8 강제
chcp 65001 && hermes chat -q "..." -s stock-analysis
```
또는 Python 내부에서:
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 4. 대용량 리포트 파일 직접 작성
- `execute_code`로 마크다운 파일 직접 생성 후 경로만 안내
- 토큰 초과(`finish_reason='length'`) 방지

### 5. Windows Python 경로 처리 (NEW - 2026-08-15)
**문제**: MSYS/Git Bash 경로(`/c/Users/...`)를 Python `open()`에 전달하면 `FileNotFoundError`
- 원인: Python은 Windows 네이티브 경로(`C:\Users\...`)만 인식
- 현상: `/c/Users/kho/주식분석/data/file.html` → `C:\c\Users\kho\주식분석\data\file.html`로 잘못 해석

**해결**:
```python
# ✅ 올바른 방법: 원시 문자열(raw string) 사용
data_dir = r"C:\Users\kho\주식분석\data"
path = os.path.join(data_dir, "naver_main_005930.html")

# ✅ 올바른 방법: pathlib 사용
from pathlib import Path
data_dir = Path(r"C:\Users\kho\주식분석\data")
path = data_dir / "naver_main_005930.html"

# ❌ 잘못된 방법: MSYS 경로 사용
data_dir = "/c/Users/kho/주식분석/data"  # Python에서 작동 안 함
```

**터미널 작업 디렉토리도 네이티브 경로로**:
```python
terminal(command="python3 parse.py", workdir=r"C:\Users\kho\주식분석")
```

## 실제 작동 확인된 명령어 (2026-08-15)
```bash
# 백그라운드 뉴스 수집 (완료 확인됨)
hermes chat -q "삼성전자(005930) 최신 뉴스 3개 요약해줘. 브라우저 쓰지 말고 web_search/web_extract만 써줘" -s stock-analysis
# → proc_24615b1d10e6, exit_code=0, 3개 기사 정상 수집

# 백그라운드 종합 리포트 (완료 확인됨)  
hermes chat -q "삼성전자(005930) 최신 뉴스/재무/계약 현황 수집해서 종합 투자 분석 리포트 만들어줘. 브라우저 쓰지 말고 web_search/web_extract만 써줘. 리포트는 옵시디언에 저장해줘" -s stock-analysis
# → proc_fd6f40ea72a8, exit_code=0, 9분 54초 소요, 옵시디언 저장 완료

# 10개 종목 배치 수집 (curl 루프, 브라우저 미사용)
for code in 005930 252670 453830 225460 011790 047040; do
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://finance.naver.com/item/main.naver?code=$code" > naver_main_${code}.html
  # ... 와이즈리포트 3종 + 뉴스 수집
  sleep 2
done
for symbol in NVDY NVDA QQQ SPY; do
  curl -s -L --max-time 30 -H "User-Agent: Mozilla/5.0 ..." \
    "https://news.google.com/rss/search?q=${symbol}+stock&hl=en&gl=US&ceid=US:en" > google_news_${symbol}.xml
  sleep 2
done
# → 35개 HTML/XML 파일 수집 완료 (약 3분)
```