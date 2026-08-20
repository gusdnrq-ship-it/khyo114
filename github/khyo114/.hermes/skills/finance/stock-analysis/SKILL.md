---
name: stock-analysis
category: finance
description: 기업/종목에 대한 뉴스·영상·전문가 의견·재무제표·계약 현황을 자동 수집하고 종합 투자 분석 리포트를 생성한다.
---

## 목표
기업/종목에 대한 뉴스·영상·전문가 의견·재무제표·계약 현황을 자동 수집하고 종합 투자 분석 리포트를 생성합니다.

## 트리거
주식 분석, 기업 분석, 재무제표 조회, 뉴스 요약, 계약 현황 확인 등 투자 리서치 관련 작업 요청 시 이 스킬을 사용합니다. 단순 질문("PER이 뭐야?")은 직접 응답 가능.

## 사용법
이 스킬은 다음과 같은 작업을 수행할 수 있습니다:
1.  **기업/종목 정보 수집**: 지정된 기업이나 종목에 대한 최신 뉴스, 영상, 전문가 의견을 웹에서 검색하고 수집합니다.
2.  **재무제표 조회**: 필요한 경우 기업의 재무제표 정보를 찾아 요약합니다.
3.  **계약 현황 확인**: 기업의 중요한 계약 현황 정보를 검색하고 분석합니다.
4.  **종합 투자 분석 리포트 생성**: 수집된 모든 정보를 바탕으로 종합적인 투자 분석 리포트를 생성합니다.

## 단계
1.  **정보 요청 분석 및 목표 설정**: 사용자의 요청을 분석하여 어떤 종류의 정보(뉴스, 재무제표, 계약 현황 등)가 필요한지 파악하고, 구체적인 정보 수집 목표를 설정합니다. 특히 비상장 기업이나 모호한 용어(예: "프리미엄")의 경우, 해당 용어의 의미를 정의하기 위한 추가 검색 계획을 수립합니다.
2.  **초기 �� 정보 수집**: `terminal` + `curl`로 정적 HTML/XML 1차 수집 (브라우저 완전 배제). 검증된 소스: 네이버 금��, 와이즈리포트/FnGuide, Google News RSS. 상세 명령어는 `references/curl-collection-pattern.md` 참조.
3.  **상세 정보 추출 및 확인**: `web_extract` 도구를 사용하여 검색 결과 URL에서 내용을 추출하고, 핵심 정보를 요약합니다. 필요한 경우 `browser_navigate`를 통해 �� 페이지에 직접 접근하여 동적인 콘텐츠를 확인하고, `browser_snapshot`으로 페이지 구조를 파악하며, `browser_console`을 통해 JavaScript 오류나 추가 데이터 로딩 여부를 확인합니다. **브라우저는 최후의 수단으로만 1~2회 제한 사용**.
4.  **데이터 정제 및 가공**: 추출된 비정형 ���스트 데이터에서 핵심적인 사실(날짜, 수치, 출처, 관련 인물 등)을 식별하고 정제합니다. 필요한 경우 Python 스크립트(`execute_code`)를 활용하여 데이터 파싱 및 구조화를 수행합니다. BeautifulSoup + regex 패턴은 `references/curl-collection-pattern.md`의 "파싱 전략" 참조.
5.  **정보 종합 및 분석**: 수집되고 정제된 모든 데이터를 종합하여 사용자가 요청한 분석 리포트 또는 답변을 구성합니다. 이때, 비상장 기업의 경우 언론 보도, 투자 기관 리포트, 장외 시장 동향 등을 종합하여 기업 가치 및 "프리미엄"의 의미를 해석합니다.
6.  **결과 보고**: 분석 결과를 사용자에게 명확하고 이해하기 쉽게 전달합니다. 필요에 따라 참고 자료의 출처를 함께 제공합니다. **대용량 리포트는 `execute_code`로 마크다운 파일 직접 작성 후 경로만 안내** (토�� 초과 방지). ��시디언 저장 규칙은 `references/obsidian-report-pattern.md` 참조.

## 도구
*   `terminal` + `curl`: 정적 HTML/XML 수집 (�� 검색 대체, 브라우저 미사용). `web_search`/`web_extract` 도구는 현재 환경에서 사용 불가.
*   `browser` ����� (`browser_navigate`, `browser_snapshot`, `browser_console`, `browser_click`, `browser_type`): **최후의 수단**으로만 사용 (타임아웃/인코딩 이슈 빈번). 동적 ��더링 필수 구간만 1~2회 제한.
*   `execute_code` / Python 스크립트: HTML/XML 파싱, 데이터 정제, 리포트 파일 직접 작성 (토�� 초과 방지).

## ⚠️ 알려진 이슈 및 해결책 (Pitfalls)

### 0. Hermes 크론 잡 설정 필수 체크리스트 (이 세션에서 검증됨)
**크론 잡이 실패하는 가장 흔한 원인은 모델/프로바이더 설정 누락입니다.**

| 설정 항목 | 필수 여부 | 권장 값 | 설정 방법 |
|-----------|-----------|---------|-----------|
| **주 모델** | ✅ | `google/gemini-2.5-flash` / `google` | `hermes model` 또는 `config.yaml` |
| **폴백 체인** | ✅ | OpenRouter + Google | `config.yaml` `model.fallback_chain` |
| **크론 전용 모델** | ✅ | `google/gemini-2.5-flash` / `google` | `hermes cron edit --model --provider` 또는 `config.yaml` `cron.model` |
| **GOOGLE_API_KEY** | ✅ | Google AI Studio 키 | `.env`에 `GOOGLE_API_KEY=...` |
| **OPENROUTER_API_KEY** | ⚠️ (폴백용) | OpenRouter 키 | `.env`에 `OPENROUTER_API_KEY=...` |
| **텔레그램 봇** | ⚠️ (알림용) | 봇 토큰 + 챗 ID | `@BotFather` → `/start` 필수 |

**config.yaml 필수 구조:**
```yaml
model:
  default: google/gemini-2.5-flash
  provider: google
  base_url: https://generativelanguage.googleapis.com/v1beta
  fallback_chain:
    - provider: openrouter
      model: google/gemini-2.5-flash
    - provider: google
      model: gemini-2.5-pro

cron:
  model: google/gemini-2.5-flash
  model_provider: google
```

**크론 잡 생성/수정 시 모델 명시:**
```bash
hermes cron edit <job_id> --model google/gemini-2.5-flash --provider google
```

> **이 세션에서 확인**: 원래 잡(e70a7a1f1729)은 NVIDIA로 성공했으나, 새 잡(96aa87e21ec6)은 OpenRouter API 키 없음으로 실패. 주 모델을 Google Gemini로, 폴백에 OpenRouter 추가 후 해결됨.

### 1. 크론 잡에서 `execute_code` 내 `terminal` 호출 차단
**증상**: 크론 잡 환경에서 `execute_code`를 사용하여 `terminal` 툴을 호출하는 Python 코드를 실행할 때 'BLOCKED: execute_code runs arbitrary local Python (including subprocess calls that bypass shell-string approval checks). Cron jobs run without a user present to approve it.' 오류로 인해 스크립트 실행이 중단됩니다.
**원인**: 크론 잡은 사용자 상호작용 없이 실행되므로, `execute_code` 내에서 잠재적으로 위험한 셸 명령을 호출하는 것을 보안상의 이유로 차단합니다. 이는 `hermes_tools.terminal` 함수를 직접 호출하는 파이썬 코드에도 적용됩니다.
**해결**: `curl`과 같은 셸 명령은 `execute_code` 대신 `default_api.terminal`을 직접 여러 번 호출하여 실행해야 합니다. 필요한 경우 `execute_code`를 사용하여 복잡한 셸 명령 문자열을 생성한 후, 생성된 명령을 `default_api.terminal`로 직접 전달하는 패턴을 사용합니다. (이 세션에서 검증됨)

### 2. 브라우저 네비게이션 과다로 인한 타임아웃 (Windows 환경)
**증상**: `browser_navigate`를 다중 호출(5~7회 이상)하면 300초(기본) 타임아웃 초과 및 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbf` 발생
**원인**: 
- Windows Git Bash 환경에서 브라우저 프로세스 실행 시 인코딩 충돌(cp949 vs utf-8)
- 동적 페이지 로딩 대기 시간 누적
**해결**:
- **1단계**: `terminal` + `curl`로 정적 HTML/XML 1차 수집 (브라우저 완전 배제)
- **2단계**: 필수 동적 콘텐츠만 `browser_navigate` 1~2회로 제한
- **타임아웃 증량**: `hermes chat -q "..." --timeout 600` 또는 세션 내 `terminal(timeout=600)`
- **인코딩 강제**: 터미널 실행 전 `chcp 65001` 또는 Python `sys.stdout.reconfigure(encoding='utf-8')`

### 3. Windows 환경에서 Python 스크립트 경로 해결 문제
**증상**: `/c/Users/...` 형태의 MSYS 경로가 Python에서 `FileNotFoundError` 발생 (`C:\\c\\Users\\...`로 잘못 해석)
**원인**: Git Bash의 `/c/...` 경로 형식이 Windows Python에서 네이티브 경로(`C:\...`)로 자동 변환되지 않음
**해결**:
- Python 스크립트 내부에서 `os.path.join` 사용 시 원시 문자열(r'C:\Users\...') 또는 `pathlib.Path` 사용
- `terminal` 호출 시 작업 디렉토리를 `C:\Users\kho\주식분석` 같은 네이티브 경로로 지정
- 데이터 디렉토리 경로는 스크립트 상단에서 `data_dir = r"C:\Users\kho\주식분석\data"` 같이 하드코딩하거나 환경변수로 주입

### 4. 금�� 사이트 접근 차단 (네이버 금��, 구글 검색 등)
**증상**: HTTP 403 Forbidden, CAPTCHA 페이지 반환
**해결**:
- `terminal` + `curl` + User-Agent 헤더로 정적 수집 (브라우저 우회)
- Google News RSS / 네이버 뉴스 RSS 활용
- User-Agent 로테이션, 요청 간격 1~2초 조절

### 5. 대용량 리포트 생성 시 출력 토�� 초과
**증상**: `finish_reason='length'`로 응답 잘림
**해결**:
- 리포트를 ��션별로 분할 생성 후 합치기
- `execute_code`로 마크다운 파일 직접 작성 후 사용자에게 경로만 안내

### 4. 정적 HTML 파싱 한계 (JavaScript 동적 ��더링 콘텐츠)
**증상**: 네이버 금�� 메인 페이지에서 현재가, 전일대비 등 핵심 시세 데이터가 정적 HTML에 없음 (플레이스��더만 존재)
**원인**: React/JS 기반 동적 ��더링으로 실제 값은 브라우저에서 JS 실행 후 채워짐
**해결**:
- 와이즈리포트(FnGuide)에서 동일 지표(EPS, BPS, PER, PBR, 배당수익률 등) 보완 수집
- 네이버 금�� 모바일 버전(m.stock.naver.com) 또는 API 엔드포인트 직접 호출 검토
- `references/curl-collection-pattern.md`의 "파싱 전략" ��션 참조

### 5. 한국 금융 사이트 인코딩 문제 (CP949/EUC-KR)
**증상**: `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbb` (또는 0xbf) 발생 시 HTML 파일 읽기 실패
**원인**: 네이버 금융, 와이즈리포트 등 국내 금융 사이트가 UTF-8이 아닌 CP949(EUC-KR)로 인코딩된 HTML 반환
**해결**:
```python
# Python 파일 읽기 시 인코딩 폴백 패턴
try:
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
except UnicodeDecodeError:
    with open(filepath, 'r', encoding='cp949') as f:
        html = f.read()
```
- `terminal` + `curl`로 수집 시 `--output` 대신 리다이렉션(`>`) 사용하면 원본 바이트 그대로 저장됨
- 파싱 단계에서 위 폴백 패턴으로 안전하게 디코딩

### 6. ETF 종목의 와이즈리포트 데이터 부재
**증상**: KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460) 등 ETF/소형주에서 와이즈리포트 기업개요/재무분석/밸류에이션 페이지가 138 bytes 빈 페이지 반환
**원인**: 와이즈리포트가 ETF나 시가총액 작은 종목에 대해 재무데이터를 제공하지 않음
**해결**:
- 밸류에이션 페이지(`c1030001.aspx`)만 활용 (일부 지표는 제공될 수 있음)
- 네이버 금융 메인 페이지의 시세 테이블에서 PER, PBR, 시가배당률, 시가총액 등 기본 지표 보완
- ETF의 경우 순자산가치(NAV), 추적오차, 운용보수 등 ETF 전용 지표 별도 수집 필요

### 7. Hermes 크론 잡 모델/프로바이더 드리프트 (Configuration Drift)
**증상**: 크론 잡 실행 시 `RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created (provider 'nvidia' -> 'gemini'; model 'nvidia/nemotron-3-ultra-550b-a55b' -> 'gemini-2.5-flash'), and this job is unpinned.`
**원인**: 크론 잡 생성 시점의 모델/프로바이더(`provider_snapshot`, `model_snapshot`)와 현재 전역 설정(`config.yaml`의 `model.default`, `model.provider`)이 다를 때, 잡이 "unpinned" 상태면 실행 차단됨.
**해결**: 크론 잡에 모델/프로바이더를 명시적으로 핀(pin) 고정해야 함.

**방법 1: `cronjob` 툴로 명시적 업데이트 (권장)**
```bash
cronjob action=update job_id=<job_id> provider=google model=gemini-2.5-flash
```

**방법 2: `jobs.json` 직접 수정**
```bash
# ~/.hermes/cron/jobs.json에서 해당 잡의 model/provider 필드 채우기
"model": "gemini-2.5-flash",
"provider": "google",
```

**방법 3: 크론 잡 생성 시 명시적 지정**
```bash
hermes cron create "30 9 * * *" "프롬프트" \
  --skill stock-analysis \
  --model google/gemini-2.5-flash \
  --provider google \
  --name "일일 주식분석 리포트"
```

**예방**: `config.yaml`에 `cron.model` / `cron.model_provider` 설정으로 기본값 강제
```yaml
cron:
  model: google/gemini-2.5-flash
  model_provider: google
```

**참조**: `references/hermes-cron-model-pin.md` — 상세 가이드, OpenRouter 무료 티어 한도(HTTP 402) 대응 전략 포함

### 7b. OpenRouter 무료 티어 한도 (HTTP 402 에러)
OpenRouter로 전환 후에도 무료 크레딧 한도에 걸릴 수 있습니다:
```
RuntimeError: HTTP 402: This request requires more credits, or fewer max_tokens. You requested up to 65535 tokens, but can only afford 16000.
```
**대응**: 더 저렴한 무료 모델(`google/gemini-2.5-flash-lite`, `deepseek/deepseek-chat`, `:free` 접미사 모델) 사용, 또는 Google Gemini 할당량 리셋 대기(UTC 자정). 상세: `references/hermes-cron-model-pin.md`의 "OpenRouter 무료 티어 한도" 섹션 참조.
**증상**: `python parse_all.py --ticker 005930` 실행 시 `error: unrecognized arguments: --ticker` 발생
**원인**: `parse_all.py`는 `--data-dir`, `--output` 인자만 받으며, 내부 `stocks` 딕셔너리에 하드코딩된 모든 종목을 한 번에 파싱함.
**해결**: `--ticker` 없이 전체 실행 후 필요한 종목만 필터링
```bash
# 전체 파싱 (하드코딩된 10개 종목 모두)
python parse_all.py --data-dir "C:\\path\\to\\data" --output "C:\\path\\to\\parsed_all.json"

# 특정 종목만 파싱하려면 스크립트 내 stocks 딕셔너리 수정 후 실행
```

### 9. GitHub Actions Runner에서 Hermes 설치 및 실행
**증상**: GitHub Actions ubuntu-latest runner에서 `hermes` 명령어 미인식, API 키 누락
**원인**: GitHub Actions runner는 깨끗한 환경이라 Hermes 미설치, 시크릿 미전달
**해결**: 워크플로우에 설치 단계와 환경변수 추가
```yaml
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: Install Hermes
        run: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
      
      - name: Configure Hermes Model (OpenRouter Free)
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          hermes config set model.default google/gemma-2-9b-it:free
          hermes config set model.provider openrouter
          hermes config set model.base_url https://openrouter.ai/api/v1
      
      - name: Run Stock Analysis
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: hermes chat -q "stock-analysis 스킬로 10종목 분석"
      
      - name: Send Telegram Notification
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          if [ -z "${TELEGRAM_CHAT_ID}" ]; then
            echo "ERROR: TELEGRAM_CHAT_ID is empty!"
            exit 1
          fi
          curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="📊 일일 주식 리포트 완료" \
            -d parse_mode="Markdown"
```

**필수 GitHub Secrets:**
- `OPENROUTER_API_KEY` (필수 - Google API 무료 티어 한도 회피)
- `TELEGRAM_BOT_TOKEN` (필수)
- `TELEGRAM_CHAT_ID` (필수)

**핵심 포인트:**
- **Step-level `env:` 사용** (job-level env에서는 시크릿이 step에 전달 안 됨)
- **Telegram은 `appleboy/telegram-action` 대신 직접 `curl` 사용** (더 안정적, 시크릿 전달 이슈 회피)
- **OpenRouter 무료 모델 사용**: `google/gemma-2-9b-it:free` (2024-08 기준 작동 확인), `meta-llama/llama-3.1-8b-instruct:free`는 유료 전환됨
- **Google API 무료 티어**는 하루 20회 한도로 Hermes 세션 1회에도 부족 → OpenRouter 필수

### 10. Windows/WSL에서 Hermes Python 환경으로 스크립트 실행
**증상**: WSL에서 `python3` 명령어로 Hermes 가상환경의 패키지(bs4, lxml 등) 사용 불가
**원인**: 시스템 Python(/usr/bin/python3)과 Hermes 가상환경 Python이 다름
**해결**: Hermes 가상환경의 Python 실행파일 사용
```bash
# WSL에서
/mnt/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe \
  /mnt/c/Users/kho/AppData/Local/hermes/skills/finance/stock-analysis/scripts/parse_all.py \
  --data-dir "/mnt/c/Users/kho/주식분석/data" \
  --output "/mnt/c/Users/kho/주식분석/data/parsed_all.json"

# 또는 PowerShell에서
C:\Users\kho\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe \
  C:\Users\kho\AppData\Local\hermes\skills\finance\stock-analysis\scripts\parse_all.py \
  --data-dir "C:\Users\kho\주식분석\data" \
  --output "C:\Users\kho\주식분석\data\parsed_all.json"
```

**핵심**: Hermes 설치 시 생성된 가상환경의 Python을 사용해야 bs4, lxml 등 설치된 패키지 사용 가능

---

## ��� 참조 파일
- `references/windows-browser-timeout-fix.md` — Windows 브라우저 타임아웃/인코딩 이슈 재현 레시피 및 수정 패턴 (백그라운드 실행, 브라우저 배제, 인코딩 강제, 파일 직접 작성 패턴 포함)
- `references/korea-finance-sources.md` — 한국 금�� 데이터 수집용 검증된 소스/RSS/선택자 목록 (네이버금��, 와이즈리포트/FnGuide, 네이버뉴스, Google News RSS + 작동 확인된 curl 명령어)
---

### 10. yfinance 데이터 수집 한계 (2026-08-20 세션 확인)
**증상**: 한국 종목 중 중소형주/ETF에서 yfinance 데이터 미지원 또는 부족
**확인된 종목**:
- TIGER K방산&우주(453830.KS/.KQ): 404 Not Found, 티커 미지원
- 우리로(046970.KS): 21일만 제공 (최소 60일 필요로 백테스트 불가)
- 토박스코리아(225460.KS): 미테스트 (예상: 데이터 없음)
**대안**: 네이버 금융 API 직접 호출 또는 KRX 공식 데이터 활용 검토 필요

---

### 11. GitHub Actions Hybrid Architecture (2026-08-20)

**Problem**: Local Hermes cron jobs require PC on 24/7. User wants free 24/7 execution.

**Solution**: Hybrid — GitHub Actions (daily batch) + Local WSL (intraday signals).

#### GitHub Actions Daily Batch Workflow (`.github/workflows/daily-stock.yml`)

```yaml
name: Daily Stock Analysis Pipeline

on:
  schedule:
    - cron: '30 0 * * *'        # 09:30 KST — Integrated fundamental + technical
    - cron: '0 22 * * 0-4'      # 07:00 KST — News filtering (weekdays)
    - cron: '0 1 * * *'         # 10:00 KST — Skill hub monitoring
    - cron: '0 17 * * *'        # 02:00 KST — Obsidian organize
  workflow_dispatch:
    inputs:
      job_type:
        type: choice
        options: [all, fundamental, technical, news, skillhub, obsidian]

env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}

jobs:
  integrated-analysis:      # 09:30 KST — Google Gemini direct (free tier)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
      - run: pip install yfinance pandas numpy pyyaml
      - run: |
          hermes config set model.default gemini-2.5-flash
          hermes config set model.provider google
      - run: |
          hermes chat -q "stock-analysis 스킬로 10종목 분석..." --skill stock-analysis,technical-trading,hermes-stock-pipeline --provider google --model gemini-2.5-flash
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add 주식분석/ || true
          git commit -m "📊 일일 주식 분석 리포트 $(date +%Y%m%d)" || true
          git push || true
      - uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: "📊 [GitHub Actions] 일일 주식 분석 완료 — ${{ job.status }}"

  news-filtering:           # 07:00 KST — NVIDIA NIM (550B + 70B fallback)
  skill-hub-monitoring:     # 10:00 KST — NVIDIA NIM
  obsidian-organize:        # 02:00 KST — NVIDIA NIM
  technical-signal-snapshot:# 09:30 KST — NVIDIA NIM (daily snapshot)
  summary:                  # Combined Telegram notification
```

**Key patterns:**
- **Explicit model/provider per job** — prevents model drift
- **Google Gemini direct** — free tier, no OpenRouter credits needed
- **NVIDIA NIM with 70B fallback** — `fallback.model` + `fallback.provider` config
- **Git commit/push** — reports committed to repo for Obsidian sync
- **`workflow_dispatch` with `job_type`** — manual runs of specific jobs

#### Required GitHub Secrets
```
GOOGLE_API_KEY        # https://aistudio.google.com/app/apikey
TELEGRAM_BOT_TOKEN    # @BotFather
TELEGRAM_CHAT_ID      # numeric (e.g., 6723387878)
NVIDIA_API_KEY        # https://build.nvidia.com
OPENROUTER_API_KEY    # optional fallback
```

#### Local WSL Cron (Intraday — 30 min intervals)
- `*/30 9-15 * * 1-5` — technical signal monitoring during market hours
- Uses Hermes venv Python explicitly (system Python 3.14 fails with numpy)
- Only runs when PC is on
- Updates `.signal_states.json` locally, synced via Git

#### Hybrid Sync Pattern
```
GitHub Actions (cloud) → Commits reports to repo
         ↓
Local PC (manual or cron) → git pull → Obsidian reads local files
```

#### Validated 2026-08-20
- Workflow file deployed to repo root `.github/workflows/daily-stock.yml`
- GitHub Actions infrastructure installs successfully (Hermes + Python + ffmpeg + ripgrep)
- Telegram test message delivered (message_id 30)
- Model selection critical: `meta-llama/llama-3.1-8b-instruct:free` no longer free on OpenRouter → replaced with Google Gemini direct + NVIDIA NIM fallback
- 6-job workflow structure verified: integrated-analysis, news-filtering, skill-hub-monitoring, obsidian-organize, technical-signal-snapshot, summary
- Manual trigger via `workflow_dispatch` with `job_type` input works
- **Workflow file MUST be at repo root `.github/workflows/`** — subdirectory paths (e.g., `github/khyo114/.github/workflows/`) are ignored by GitHub Actions
- System Python 3.14 incompatible with numpy C-extensions → workflows must use Hermes venv Python explicitly: `/home/runner/.hermes/bin/hermes` or `source ~/.bashrc && hermes`
- `workflow_dispatch` inputs with `type: choice` and `options` array works correctly for manual job selection
- **yfinance Korean small caps/ETFs unsupported**: 우리로(046970) 21 days only, TIGER K방산&우주(453830) 404, 토박스코리아(225460) expected unsupported — need alternative data source (Naver Finance API, KRX)
- parse_all.py has extra ticker Daewoo (047040) not in pipeline spec — watchlist externalization to config/watchlist.yaml prioritized

**See `references/github-actions-deployment-pitfalls.md` for complete deployment pitfalls checklist and hybrid architecture documentation.**

---

### 12. Watchlist Externalization (Planned → Implemented in templates)

Move hardcoded tickers from prompts to **`config/watchlist.yaml`** (version controlled):

```yaml
# config/watchlist.yaml
fundamental:
  domestic: ["005930", "252670", "453830", "225460", "011790"]
  overseas: ["NVDY", "NVDA", "QQQ", "TQQQ", "AAPL"]

technical:
  domestic: ["005930", "000660", "011790", "046970", "252670", "453830", "225460", "373220", "006400", "035420", "035720", "005380"]
  overseas: ["NVDA", "NVDY", "QQQ", "TQQQ", "AAPL", "MSFT", "GOOGL", "AMZN"]

unsupported_by_yfinance:
  - "453830"  # TIGER K방산&우주
  - "046970"  # 우리로
  - "225460"  # 토박스코리아
```

**Benefits:** Single source of truth, easy to modify, version controlled, CI can validate.

See `templates/watchlist.yaml` in `hermes-stock-pipeline` skill for full 92-ticker list.

---

## 📁 지원 파일 (References, Templates, Scripts)

### References
- `references/curl-collection-pattern.md` — `terminal` + `curl`로 정적 HTML/XML 수집 및 BeautifulSoup 파싱 패턴 (인코딩 폴백, ETF 처리 포함)
- `references/korea-finance-sources.md` — 한국 금융 데이터 수집용 검증된 소스/RSS/선택자 목록 (네이버금융, 와이즈리포트/FnGuide, 네이버뉴스, Google News RSS + 작동 확인된 curl 명령어)
- `references/obsidian-report-pattern.md` — 옵시디언 저장 및 리포트 생성 패턴 (크론 자동화, 템플릿 참조)
- `references/windows-browser-timeout-fix.md` — Windows 브라우저 타임아웃/인코딩 이슈 재현 레시피 및 수정 패턴
- `references/hermes-cron-model-pin.md` — 크론 잡 모델/프로바이더 핀 고정 가이드
- `references/integrated-watchlist-config.md` — 통합 감시 리스트 설정
- `references/openrouter-free-models.md` — OpenRouter 무료 모델 목록
- `references/integrated-pipeline-pattern.md` — 펀더멘털+기술적 통합 파이프라인 실행 패턴
- `references/session-2026-08-20-github-actions-deployment.md` — **GitHub Actions hybrid architecture deployment & validation (2026-08-20)**

### Templates
- `templates/integrated_report_template.md` — 통합 리포트 마크다운 템플릿
- `templates/individual_report_template.md` — 개별 종목 리포트 마크다운 템플릿

### Scripts
- `scripts/parse_all.py` — 전체 종목 파싱 스크립트 (네이버+와이즈리포트+Google RSS, 인코딩 폴백 내장)
- `scripts/generate_reports.py` — 파싱된 JSON으로부터 리포트 생성 스크립트 (옵시디언 규칙 준수)

사용 예:
```bash
# 1. 데이터 수집 (curl로 사전 수집 후)
python scripts/parse_all.py --data-dir "C:\Users\kho\주식분석\data" --output "C:\Users\kho\주식분석\data\parsed_all.json"

# 2. 리포트 생성
python scripts/generate_reports.py --parsed "C:\Users\kho\주식분석\data\parsed_all.json" --obsidian-dir "C:\Users\kho\주식분석"
```

## 예시 명령
*   "SpaceX의 최신 뉴스를 요약해 줘."
*   "테슬라의 최근 재무제표를 알려줘."
*   "삼성전자의 주요 계약 현황은 어때?"
*   "SK하이닉스에 대한 종합 투자 분석 리포트를 작성해 줘."

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08-16 | Initial stock analysis skill with news, financials, expert opinions |
| 1.1.0 | 2026-08-18 | Added pipeline integration with technical-trading, cron setup |
| 1.2.0 | 2026-08-20 | First integrated pipeline run: 10 fundamental reports, Daewoo (047040) extra ticker, yfinance limits for KR small caps/ETFs documented |
| 1.3.0 | 2026-08-20 | Second integrated pipeline run confirmed: 10 fundamental + 4 technical reports, NVDA BUY signal highlighted in Telegram, parse_all.py ticker list mismatch (Daewoo not in pipeline spec), watchlist externalization prioritized |
