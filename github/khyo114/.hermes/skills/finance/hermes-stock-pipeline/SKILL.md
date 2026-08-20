---
name: hermes-stock-pipeline
description: "End-to-end stock analysis pipeline with Hermes: cron jobs, GitHub Actions, Telegram notifications, and Obsidian storage"
category: finance
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [hermes, stock-analysis, cron, github-actions, telegram, obsidian, pipeline]
---

# Hermes Stock Analysis Pipeline

End-to-end automated stock analysis pipeline using Hermes Agent with scheduled cron jobs, GitHub Actions backup, Telegram notifications, and Obsidian vault storage.

## Overview

This skill provides a complete production-ready pipeline for daily stock analysis:
- **Local cron** (primary): Runs daily at 09:30 KST via Hermes gateway
- **GitHub Actions** (backup): Runs daily at 09:30 KST via cloud runner
- **Telegram notifications**: Delivery to configured chat
- **Obsidian storage**: Structured markdown files with tags
- **Multi-provider LLM**: Google Gemini primary + OpenRouter fallback

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Hermes Gateway │────▶│  stock-analysis  │────▶│   Obsidian      │
│  (cron 09:30)   │     │  skill           │     │  Vault          │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram Bot   │     │  GitHub Actions  │     │  Markdown Files │
│  Notifications  │     │  (backup runner) │     │  + Tags         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Prerequisites

- Hermes Agent v0.20.1+
- Google AI Studio API key (primary)
- OpenRouter API key (fallback, optional)
- Telegram Bot (via @BotFather)
- Obsidian vault path configured
- GitHub repository (for Actions backup)

## Configuration

### 1. Hermes Config (`~/.hermes/config.yaml`)

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
  context_length: 200000

cron:
  model: google/gemini-2.5-flash
  model_provider: google

display:
  interface: tui
  skin: "dark"
  font_family: "JetBrains Mono"
  font_size: 14

terminal:
  backend: local
  cwd: .
  timeout: 180
  env:
    LANG: "C.UTF-8"
    LC_ALL: "C.UTF-8"
    PYTHONIOENCODING: "utf-8"

web:
  backend: firecrawl
```

### 2. Environment Variables (`~/.hermes/.env`)

```bash
GOOGLE_API_KEY=your_google_ai_studio_key
OPENROUTER_API_KEY=your_openrouter_key  # optional
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_numeric_chat_id
```

### 3. Cron Job Setup

```bash
# Create daily cron job (09:30 KST)
hermes cron create "30 9 * * *" \
  "stock-analysis 스킬로 10종목 분석 후 옵시디언 저장" \
  --skill stock-analysis \
  --name "일일 주식분석 리포트 (10종목)" \
  --deliver origin
```

### 4. Telegram Bot Setup

```bash
# 1. Create bot via @BotFather
# 2. Get token and chat ID
# 3. Configure in Hermes
hermes gateway setup
# Select Telegram → enter token → enter chat ID
```

### 5. GitHub Actions Backup (`.github/workflows/stock.yml`)

```yaml
name: Daily Stock
on:
  schedule:
    - cron: '30 0 * * *'  # UTC 00:30 = KST 09:30
  workflow_dispatch:
jobs:
  run:
    runs-on: ubuntu-latest
    env:
      GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
    steps:
      - name: Install Hermes
        run: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
      - name: Run Stock Analysis
        run: hermes chat -q "stock-analysis 스킬로 10종목 분석"
      - name: Send Telegram Notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: "📊 일일 주식 리포트 완료"
```

**GitHub Secrets required:**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GOOGLE_API_KEY`
- `OPENROUTER_API_KEY` (optional)

### 6. Production GitHub Actions Workflow (`.github/workflows/daily-stock.yml`)

Full-featured workflow with **4 parallel jobs** covering the complete pipeline:

```yaml
name: Daily Stock Analysis Pipeline

on:
  schedule:
    # 09:30 KST = 00:30 UTC — Integrated fundamental + technical
    - cron: '30 0 * * *'
    # 07:00 KST = 22:00 UTC (prev day) — News filtering
    - cron: '0 22 * * 0-4'
    # 10:00 KST = 01:00 UTC — Skill hub monitoring
    - cron: '0 1 * * *'
    # 02:00 KST = 17:00 UTC (prev day) — Obsidian organize
    - cron: '0 17 * * *'
  workflow_dispatch:
    inputs:
      job_type:
        description: 'Which job to run'
        required: true
        default: 'all'
        type: choice
        options: [all, fundamental, technical, news, skillhub, obsidian]

env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
  LANG: ko_KR.UTF-8
  LC_ALL: ko_KR.UTF-8
  PYTHONIOENCODING: utf-8

jobs:
  # 1. Fundamental + Technical Integrated (09:30 KST)
  integrated-analysis:
    if: github.event_name == 'schedule' || inputs.job_type == 'all' || inputs.job_type == 'fundamental'
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install Hermes
        run: |
          curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
          echo "$HOME/.hermes/bin" >> $GITHUB_PATH
      - name: Install deps
        run: pip install yfinance pandas numpy pyyaml
      - name: Configure Hermes (Google Gemini direct — free, no credits)
        run: |
          hermes config set model.default gemini-2.5-flash
          hermes config set model.provider google
      - name: Run Integrated Analysis
        run: |
          hermes chat -q "
          stock-analysis 스킬로 10종목 분석 후 기술적 분석 5종목 백테스트 수행
          ## 1단계: 펀더멘털 (stock-analysis) — 10종목
          - 국내: 삼성전자(005930), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), SKC(011790)
          - 해외: NVDY, NVDA, QQQ, TQQQ, AAPL
          ## 2단계: 기술적 (technical-trading) — 5종목
          - 삼성전자, NVDA, 우리로(046970), SKC, TIGER K방산&우주
          ## 3단계: 통합 리포트 + Obsidian 경로
          " --skill stock-analysis,technical-trading,hermes-stock-pipeline --provider google --model gemini-2.5-flash
      - name: Commit & Push Reports
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add 주식분석/ || true
          git commit -m "📊 일일 주식 분석 리포트 $(date +%Y%m%d)" || true
          git push || true
      - name: Telegram Notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: |
            📊 [GitHub Actions] 일일 주식 분석 완료
            상태: ${{ job.status }}

  # 2. News/Disclosure Filtering (07:00 KST)
  news-filtering:
    if: github.event_name == 'schedule' || inputs.job_type == 'all' || inputs.job_type == 'news'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install Hermes
        run: |
          curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
          echo "$HOME/.hermes/bin" >> $GITHUB_PATH
      - name: Install deps
        run: pip install yfinance pandas numpy pyyaml feedparser requests
      - name: Configure Hermes (NVIDIA NIM with fallback)
        run: |
          hermes config set model.default nvidia/nemotron-3-ultra-550b-a55b
          hermes config set model.provider nvidia
          hermes config set fallback.model nvidia/llama-3.1-nemotron-70b-instruct
          hermes config set fallback.provider nvidia
      - name: Run News Filtering
        run: |
          hermes chat -q "
          뉴스/공시 필터링 → 내 92종목만 추출
          ## 국내 49개 + 해외 43개 티커 하드코딩
          ## DART + 네이버/다음 + Yahoo Finance
          ## 티커 매칭 → 중요도 → LLM 요약
          " --skill stock-analysis,hermes-stock-pipeline --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b
      - name: Commit & Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add 주식분석/뉴스/ || true
          git commit -m "📰 뉴스 필터링 $(date +%Y%m%d)" || true
          git push || true
      - name: Telegram Notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: "📰 [GitHub Actions] 뉴스 필터링 완료 — ${{ job.status }}"

  # 3. Skill Hub Monitoring (10:00 KST)
  skill-hub-monitoring:
    if: github.event_name == 'schedule' || inputs.job_type == 'all' || inputs.job_type == 'skillhub'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install Hermes
        run: |
          curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
          echo "$HOME/.hermes/bin" >> $GITHUB_PATH
      - name: Configure Hermes (NVIDIA with fallback)
        run: |
          hermes config set model.default nvidia/nemotron-3-ultra-550b-a55b
          hermes config set model.provider nvidia
          hermes config set fallback.model nvidia/llama-3.1-nemotron-70b-instruct
          hermes config set fallback.provider nvidia
      - name: Run Skill Hub Monitoring
        run: |
          hermes chat -q "
          Hermes 스킬 허브 자동 모니터링 & 평가
          1. 허브 스캔 (hermes skills check/browse/list)
          2. 상위 10개 후보 검토
          3. hermes-agent-skill-authoring 7가지 기준 평가 (70점 이상)
          4. requesting-code-review 보안 스캔
          5. 설치 권장 스킬만 요약 전송 + Obsidian 저장
          " --skill hermes-agent-skill-authoring,requesting-code-review,hermes-agent --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b
      - name: Commit & Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add 주식분석/스킬허브/ || true
          git commit -m "🔍 스킬 허브 모니터링 $(date +%Y%m%d)" || true
          git push || true
      - name: Telegram Notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: "🔍 [GitHub Actions] 스킬 허브 모니터링 — ${{ job.status }}"

  # 4. Obsidian Vault Organize (02:00 KST)
  obsidian-organize:
    if: github.event_name == 'schedule' || inputs.job_type == 'all' || inputs.job_type == 'obsidian'
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install Hermes
        run: |
          curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
          echo "$HOME/.hermes/bin" >> $GITHUB_PATH
      - name: Configure Hermes (NVIDIA with fallback)
        run: |
          hermes config set model.default nvidia/nemotron-3-ultra-550b-a55b
          hermes config set model.provider nvidia
          hermes config set fallback.model nvidia/llama-3.1-nemotron-70b-instruct
          hermes config set fallback.provider nvidia
      - name: Run Obsidian Organize
        run: |
          hermes chat -q "
          Obsidian 볼트 자동 정리 (5레벨/넘버링/태그/99아카이브)
          대상: 주식분석/ 볼트 (GitHub 동기화 상태)
          규칙: 5레벨·넘버링·99아카이브·유동적·버전관리·태그보완·양방향링크
          " --skill obsidian,hermes-stock-pipeline --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b
      - name: Commit & Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add 주식분석/ || true
          git commit -m "🗂 Obsidian 볼트 정리 $(date +%Y%m%d)" || true
          git push || true
      - name: Telegram Notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: "🗂 [GitHub Actions] Obsidian 정리 — ${{ job.status }}"

  # 5. Technical Signal Snapshot (09:30 KST — once daily, intraday runs locally)
  technical-signal-snapshot:
    if: github.event_name == 'schedule' || inputs.job_type == 'all' || inputs.job_type == 'technical'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install Hermes
        run: |
          curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
          echo "$HOME/.hermes/bin" >> $GITHUB_PATH
      - name: Install deps
        run: pip install yfinance pandas numpy pyyaml
      - name: Configure Hermes (NVIDIA with fallback)
        run: |
          hermes config set model.default nvidia/nemotron-3-ultra-550b-a55b
          hermes config set model.provider nvidia
          hermes config set fallback.model nvidia/llama-3.1-nemotron-70b-instruct
          hermes config set fallback.provider nvidia
      - name: Run Technical Signal Snapshot
        run: |
          hermes chat -q "
          기술적 매매 시그널 스냅샷 (장중 30분마다 — GitHub에서는 1회)
          ## 20종목: 국내 12 + 해외 8
          ## 쌍굴파기 이중 BB — W패턴 6단계 진단
          ## 시그널 발생 시에만 상세 요약
          " --skill technical-trading,hermes-stock-pipeline --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b
        continue-on-error: true
      - name: Commit & Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add 주식분석/ || true
          git commit -m "🔔 기술적 시그널 스냅샷 $(date +%Y%m%d)" || true
          git push || true
      - name: Telegram Notification
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: "🔔 [GitHub Actions] 기술적 시그널 — ${{ job.status }}"

  # Summary notification
  summary:
    needs: [integrated-analysis, news-filtering, skill-hub-monitoring, obsidian-organize, technical-signal-snapshot]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Send Summary
        uses: appleboy/telegram-action@master
        with:
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          message: |
            ✅ [GitHub Actions] 일일 파이프라인 전체 완료
            - 통합 분석: ${{ needs.integrated-analysis.result }}
            - 뉴스 필터링: ${{ needs.news-filtering.result }}
            - 스킬 허브: ${{ needs.skill-hub-monitoring.result }}
            - Obsidian 정리: ${{ needs.obsidian-organize.result }}
            - 기술적 시그널: ${{ needs.technical-signal-snapshot.result }}
            실행: ${{ github.run_started_at }}
```

**Additional GitHub Secrets required:**
- `NVIDIA_API_KEY` (from https://build.nvidia.com)

---

### Hybrid Architecture: GitHub Actions (Daily Batch) + Local WSL (Intraday)

| Component | Schedule | Execution | Notes |
|-----------|----------|-----------|-------|
| **GitHub Actions** | 07:00, 09:30, 10:00, 02:00 KST | Cloud (ubuntu-latest) | **Runs even when PC is off** — daily batch jobs |
| **Local WSL Cron** | 09:00–15:30 every 30min (weekdays) | Local Hermes gateway | **Intraday technical signals** — only when PC is on |
| **Obsidian Sync** | GitHub → Local `git pull` | Manual or local cron | Reports committed to repo, pulled locally for Obsidian |

**Key insight:** GitHub Actions cannot run sub-hour cron reliably → technical signal monitoring runs locally via Hermes cron (`*/30 9-15 * * 1-5`). GitHub Actions provides the daily batch backup.

---

### Watchlist Externalization (Planned)

Move hardcoded tickers from prompts to **`config/watchlist.yaml`**:

```yaml
# config/watchlist.yaml
fundamental:
  domestic:
    - "005930"  # 삼성전자
    - "252670"  # KODEX 200
    - "453830"  # TIGER K방산&우주
    - "225460"  # 토박스코리아
    - "011790"  # SKC
  overseas:
    - "NVDY"
    - "NVDA"
    - "QQQ"
    - "TQQQ"
    - "AAPL"

technical:
  domestic:
    - "005930"  # 삼성전자
    - "000660"  # SK하이닉스
    - "011790"  # SKC
    - "046970"  # 우리로 (yfinance 미지원)
    - "252670"  # KODEX 200
    - "453830"  # TIGER K방산&우주 (yfinance 미지원)
    - "225460"  # 토박스코리아 (yfinance 미지원)
    - "373220"  # LG에너지솔루션
    - "006400"  # 삼성SDI
    - "035420"  # NAVER
    - "035720"  # 카카오
    - "005380"  # 현대차
  overseas:
    - "NVDA"
    - "NVDY"
    - "QQQ"
    - "TQQQ"
    - "AAPL"
    - "MSFT"
    - "GOOGL"
    - "AMZN"

# yfinance 미지원 종목: 별도 데이터 소스 필요
unsupported_by_yfinance:
  - "453830"  # TIGER K방산&우주
  - "046970"  # 우리로
  - "225460"  # 토박스코리아
```

**Benefits:** Single source of truth, easy to add/remove tickers, version controlled, CI can validate.

## Usage

### Manual Run (Local)

```bash
# Parse data
python3 /path/to/stock-analysis/scripts/parse_all.py \
  --data-dir "/path/to/data" \
  --output "/path/to/data/parsed_all.json"

# Generate reports
python3 /path/to/stock-analysis/scripts/generate_reports.py \
  --parsed "/path/to/data/parsed_all.json" \
  --obsidian-dir "/path/to/obsidian/vault"
```

### Via Hermes Chat

```bash
hermes chat -q "stock-analysis 스킬로 10종목 분석 후 옵시디언 저장" --skill stock-analysis --yolo
```

### Integrated Pipeline Cron Job (Fundamental + Technical)

Create a single cron job that runs both fundamental and technical analysis:

```bash
hermes cron create "30 9 * * *" \
  "통합 주식분석 파이프라인 실행 — 매일 09:30 KST

## 1단계: 펀더멘털 분석 (stock-analysis 스킬)
대상 10종목:
- 국내: 삼성전자(005930), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), SKC(011790)
- 해외: NVDY, NVDA, QQQ, (나머지 2개는 기존 설정 유지)

## 2단계: 기술적 분석 (technical-trading 스킬)
핵심 종목 5개에 대해 쌍굴파기 이중 볼린저밴드 백테스트 + 현재 시그널 진단:
- 삼성전자(005930), NVDA, 우리로(046970), SKC(011790), TIGER K방산&우주(453830)

## 3단계: 통합 알림 (Telegram)
- 펀더멘털 요약 + 기술적 요약 + Obsidian 저장 경로
- 실행 시간·소요 시간·에러 여부 포함" \
  --skill stock-analysis,technical-trading,hermes-stock-pipeline \
  --name "통합 주식분석 파이프라인 (펀더멘털 + 기술적)" \
  --model google/gemini-2.5-flash-lite \
  --provider openrouter \
  --deliver origin,telegram:6723387878
```

**핵심 포인트:**
- `--model`/`--provider` 명시로 **드래프 방지** (model drift 에러 예방)
- `--deliver origin,telegram:CHAT_ID`로 **멀티 채널 전달**
- 여러 스킬을 `--skill`에 콤마 구분으로 지정

### Intraday Technical Signal Monitoring Cron Job (30-min intervals)

Separate cron for real-time signal detection during market hours:

```bash
hermes cron create "30 9-15 * * 1-5" \
  "장중 30분마다 기술적 시그널 감시 (쌍굴파기 이중 볼린저밴드)

## 대상 20종목
- 국내 12: 삼성전자(005930), SK하이닉스(000660), SKC(011790), 우리로(046970), KODEX 200(252670), TIGER K방산&우주(453830), 토박스코리아(225460), LG에너지솔루션(373220), 삼성SDI(006400), NAVER(035420), 카카오(035720), 현대차(005380)
- 해외 8: NVDA, NVDY, QQQ, TQQQ, AAPL, MSFT, GOOGL, AMZN

## 실행 로직
1. yfinance 30분봉 수집 (최근 60일)
2. BB(20,2)+BB(20,1) 계산 + 로컬 극값 탐지
3. W-패턴 6단계 상태 머신으로 현재 단계 진단
4. Phase 5(매수) / Phase 6(매도) 발생 시에만 LLM 호출 → Telegram 3줄 요약
5. 시그널 발생 종목만 Obsidian 저장

## 모델 고정
- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b" \
  --skill technical-trading \
  --name "장중 기술적 시그널 실시간 감시 (30분 주기)" \
  --model nvidia/nemotron-3-ultra-550b-a55b \
  --provider nvidia \
  --deliver origin,telegram:6723387878
```

**First scheduled run (2026-08-20 15:01 KST)**: Job `75de09c384ee` executed successfully — 17/20 tickers processed (3 unsupported: 046970, 453830, 225460), 0 new signals, 12 tickers in Phase 2 (REBOUND), state persisted.

### Job Deduplication Pattern

기존 단일 분석 잡이 있으면 **비활성화(pause)** 후 통합 파이프라인만 유지:

```bash
# 기존 잡 조회
hermes cron list

# 기존 잡 비활성화
hermes cron pause <old_job_id>

# 통합 파이프라인만 활성 상태 유지
```

### Direct Script Execution (Windows PowerShell)

```powershell
# Parse
C:\Users\kho\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe `
  C:\Users\kho\AppData\Local\hermes\skills\finance\stock-analysis\scripts\parse_all.py `
  --data-dir "C:\Users\kho\주식분석\data" `
  --output "C:\Users\kho\주식분석\data\parsed_all.json"

# Generate reports
C:\Users\kho\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe `
  C:\Users\kho\AppData\Local\hermes\skills\finance\stock-analysis\scripts\generate_reports.py `
  --parsed "C:\Users\kho\주식분석\data\parsed_all.json" `
  --obsidian-dir "C:\Users\kho\주식분석"
```

## Obsidian Storage Structure

```
주식분석/
├── YYYYMMDD_종합투자분석리포트.md          # 통합 리포트
├── 삼성전자/
│   └── YYYYMMDD_삼성전자.md
├── KODEX 200/
│   └── YYYYMMDD_KODEX 200.md
├── NVDA/
│   └── YYYYMMDD_엔비디아.md
└── ... (각 종목별 폴더)
```

**Tags applied:** `#주식분석 #종목코드 #섹터 #시장구분 #투자리포트`

## Troubleshooting

### Cron Job Model Drift Error

```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created (provider 'nvidia' -> 'gemini'; model 'nvidia/nemotron-3-ultra-550b-a55b' -> 'gemini-2.5-flash'), and this job is unpinned.
```

**Fix:** Pin the job to current model/provider

```bash
# Edit jobs.json directly
# Set model and provider fields (not null)
{
  "model": "gemini-2.5-flash",
  "provider": "google"
}
```

Or recreate the cron job with explicit model:

```bash
hermes cron edit <job_id> --model google/gemini-2.5-flash --provider google
```

### Cron Job Created After Scheduled Time

**Symptom:** `next_run_at` shows tomorrow's date even though today's run should have happened.

**Cause:** Cron job created **after** today's scheduled execution time (e.g., created at 15:00 for a 09:30 job).

**Behavior:** Expected — scheduler calculates next run as tomorrow.

**Fix:** Run manually today, auto from tomorrow:
```bash
cronjob(action="run", job_id="<job_id>")
# or
hermes cron run <job_id>
```

### Telegram Delivery Errors

**Symptom:** `last_delivery_error: "platform 'telegram' not configured/enabled"` shown even after gateway is running.

**Cause:** Cached error from previous failed delivery attempt.

**Fix:** Ignore if gateway status shows running. Next successful run will clear it. Verify with:
```bash
hermes gateway status
```

### Gateway Won't Start on WSL (systemd)

**Symptom:** `hermes gateway status` shows "Gateway is not running" after restart.

**Cause:** WSL systemd services don't persist reliably.

**Fix:** Use Windows Startup folder method:
```bash
hermes gateway install
# Creates: C:\Users\<user>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Hermes_Gateway.vbs
hermes gateway start
```

Alternative nohup:
```bash
nohup hermes gateway run --force > ~/.hermes/gateway.log 2>&1 &
```

### NVIDIA NIM Model Not Found (HTTP 404)

**Symptom:** `HTTP 404: 404 page not found` when using NVIDIA provider.

**Cause:** Using short model name (`nemotron-3-ultra`) instead of full ID.

**Fix:** Discover available models first:
```bash
curl -s -H "Authorization: Bearer $NVIDIA_API_KEY" https://integrate.api.nvidia.com/v1/models
```
Use full ID: `nvidia/nemotron-3-ultra-550b-a55b`

See `references/nvidia-nim-model-discovery.md` for details.

### Korean Encoding Issues (Windows/WSL)

```bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONIOENCODING=utf-8
```

Add to `config.yaml`:
```yaml
terminal:
  env:
    LANG: "C.UTF-8"
    LC_ALL: "C.UTF-8"
    PYTHONIOENCODING: "utf-8"
```
(Use `C.UTF-8` — `ko_KR.UTF-8` not available in MSYS2/WSL)

### Skill Not Found Error

```
Error: Unknown skill(s): stock-analysis
```

**Fix:** Ensure skill is in correct location and enabled:
- Path: `~/.hermes/skills/finance/stock-analysis/`
- Check `hermes skills list` shows it as enabled
- Use full path if needed: `--skill /path/to/stock-analysis`

### GitHub Actions Failures

1. **API key missing**: Add `GOOGLE_API_KEY` to GitHub Secrets
2. **Telegram fails**: Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in Secrets
3. **Model not configured**: Ensure workflow has `env:` section with API keys

### Windows Path Issues in Scripts

Use raw strings or forward slashes:
```python
# Good
data_dir = r"C:\Users\kho\주식분석\data"
# Good
data_dir = "C:/Users/kho/주식분석/data"
# Bad - causes escape sequence issues
data_dir = "C:\Users\kho\주식분석\data"
```

## Scripts Reference

| Script | Purpose | Location |
|--------|---------|----------|
| `parse_all.py` | Parse HTML/XML data from financial sites | `scripts/parse_all.py` |
| `generate_reports.py` | Generate markdown reports for Obsidian | `scripts/generate_reports.py` |

### parse_all.py Usage

```bash
python parse_all.py --data-dir "PATH" --output "PATH"
# Parses all 10 hardcoded stocks
```

### generate_reports.py Usage

```bash
python generate_reports.py --parsed "PARSED_JSON" --obsidian-dir "VAULT_PATH"
# Creates individual + integrated reports
```

## References

- `references/cron-model-drift-fix.md` — Cron job model pinning patterns
- `references/integrated-pipeline-config.md` — Integrated pipeline configuration
- `references/integrated-pipeline-cron-setup.md` — Cron setup for integrated pipeline
- `references/korea-finance-sources.md` — Verified data sources (Naver, WiseReport, Google RSS)
- `references/obsidian-report-pattern.md` — Obsidian storage conventions
- `references/windows-browser-timeout-fix.md` — Windows encoding/timeout fixes
- `references/automated-skill-hub-monitoring.md` — Automated skill hub monitoring pattern (shared with hermes-agent-operations)
- `references/intraday-monitoring-cron.md` — Intraday 30-min monitoring cron job setup (2026-08-18)
- `references/yfinance-multiindex-fix.md` — yfinance MultiIndex column handling fix for pipeline (2026-08-18)
- `references/session-2026-08-18-pipeline-config.md` — Pipeline configuration session
- `references/session-2026-08-20-intraday-cron-execution.md` — First scheduled cron execution results
- `references/session-2026-08-20-integrated-pipeline.md` — **Integrated pipeline first auto-run results (2026-08-20)**
- `references/session-2026-08-20-second-run.md` — **Integrated pipeline second run results (2026-08-20)**
- `references/session-2026-08-20-github-actions-deployment.md` — **GitHub Actions hybrid architecture deployment & validation (2026-08-20)**

## Templates

- `templates/integrated_report_template.md` — Integrated report structure
- `templates/individual_report_template.md` — Individual stock report structure

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08-16 | Initial pipeline setup with cron, GitHub Actions, Telegram, Obsidian |
| 1.1.0 | 2026-08-18 | Added intraday monitoring cron job, yfinance MultiIndex fix |
| 1.2.0 | 2026-08-20 | First integrated pipeline auto-run (fundamental + technical), yfinance coverage limits documented, watchlist externalization planned |
| 1.3.0 | 2026-08-20 | Second integrated pipeline run confirmed: 10 fundamental + 4 technical reports generated, NVDA BUY signal ($212.71 entry, $198.75 stop, $222.19 target), 3 tickers unsupported by yfinance (453830, 046970, 225460), Daewoo (047040) extra ticker in parse_all.py, watchlist externalization to config/watchlist.yaml prioritized |
| 1.4.0 | 2026-08-20 | **GitHub Actions hybrid architecture deployed**: Fixed workflow path (.github/workflows/ at repo root), replaced deprecated free model with Google Gemini direct (free) + NVIDIA NIM fallback, 6-job workflow (integrated-analysis, news-filtering, skill-hub-monitoring, obsidian-organize, technical-signal-snapshot, summary), Git-based Obsidian sync (commit → push → local pull), 5 required GitHub Secrets documented. Validated: infrastructure installs work, Telegram delivery works, model selection critical (meta-llama/llama-3.1-8b-instruct:free no longer free on OpenRouter). |
| 1.5.0 | 2026-08-20 | **GitHub Actions full validation completed**: Workflow file at repo root `.github/workflows/daily-stock.yml` confirmed, 6-job structure validated (integrated-analysis 09:30 KST, news-filtering 07:00 KST, skill-hub-monitoring 10:00 KST, obsidian-organize 02:00 KST, technical-signal-snapshot 09:30 KST, summary), `workflow_dispatch` with `job_type` choice input works, model selection per-job explicit (Google Gemini direct for fundamental, NVIDIA NIM 550B+70B fallback for others), Telegram delivery via curl validated (message_id 30), Git commit/push for Obsidian sync works, system Python 3.14 incompatible with numpy → must use Hermes venv Python explicitly in workflows. |
| 1.6.0 | 2026-08-20 | **Critical GitHub Actions deployment pitfalls documented**: (1) Workflow file MUST be at repo root `.github/workflows/` — nested paths like `github/khyo114/.github/workflows/` are ignored by GitHub. (2) Free model `meta-llama/llama-3.1-8b-instruct:free` no longer works on OpenRouter — use Google Gemini direct (free, no credits) or NVIDIA NIM with API key. (3) System Python 3.14 on GitHub runners breaks numpy → must use `actions/setup-python@v5` with `python-version: '3.11'` explicitly. (4) `workflow_dispatch` inputs must be defined for manual trigger; `job_type` choice enables selective job execution. (5) Git-based Obsidian sync: Actions commits reports to repo → local `git pull` for Obsidian viewing. (6) Windows/WSL path confusion: repo root is `C:/Users/kho` not `C:/Users/kho/github/khyo114` — `git rev-parse --show-toplevel` to verify. |
| 1.7.0 | 2026-08-20 | **GitHub Actions full production validation completed**: (1) Added `permissions: contents: write` + `actions: read` to workflow — required for `git push` from Actions runner (github-actions[bot] needs write access). (2) Verified 6-job workflow execution: all jobs trigger correctly on `workflow_dispatch` with `job_type` input. (3) Model selection confirmed per-job: `integrated-analysis` uses Google Gemini direct (free, no credits), all other jobs use NVIDIA NIM 550B with 70B fallback. (4) Telegram delivery via `appleboy/telegram-action` validated (message_id 30). (5) Git commit/push from Actions to repo works for Obsidian sync. (6) `obsidian-organize` job runs on schedule (02:00 KST) independently. (7) Session tracking: `git rev-parse --show-toplevel` critical for identifying actual repo root when nested folders exist. |

---

**Maintainer:** Hermes Agent  
**Last Updated:** 2026-08-18